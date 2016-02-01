import os
import re
import mimetypes

from django.shortcuts import render
from django.shortcuts import get_object_or_404 as get_or_404

from django.http import HttpResponse as httpresp
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate

from django.conf import settings
from django.utils import timezone

from .models import Block
from .models import DrawingStatus
from .models import Department
from .models import Drawing
from .models import DrawingAttachment
from .models import Revision
from .models import RevisionAttachment
from .models import Comment
from .models import CommentAttachment
from .models import Reply
from .models import ReplyAttachment

from .forms import SearchForm
from .forms import FileForm
from .forms import DrawingAddForm
from .forms import RemoveFileForm
from .forms import RevisionAddForm
from .forms import CommentAddForm 
from .forms import ReplyAddForm

from .tasks import test

DWG_TEST = re.compile('^([a-zA-Z0-9_-]+)$')
REV_TEST = re.compile('^([a-zA-Z0-9_\.-]+)$')

#---------------------- General ------------------------
def _get_user(request):
    ''' Helper to return user from a request '''
    if request.user.is_authenticated():
        user = request.user
    else:
        user = None

    return user


def logout_view(request):
    ''' Logout confirmation '''
    user = request.user
    logout(request)
    return render(request, 'tracking/logout.html', {'username':user})
    # return httpresp('''Goodbye {} !<br>
    #                 You\'ve successfully logged out!<br>
    #                 <a href="/">return to homepage</a>'''.format(user))


#---------------------- Index ------------------------
@login_required
def index(request):
    ''' Homepage '''
    user = _get_user(request)
    t = test.delay('words')
    # print(t.get())
    return render(request, 'tracking/index.html', {'username':user})


#---------------------- Quicklinks ------------------------
@login_required
def open_comment_search(request):
    user = _get_user(request)
    coms = Comment.objects.prefetch_related('revision')\
                         .filter(status=True)
    context = {'comments':coms, 'username':user}
    return render(request, 'tracking/open_comments.html', context)


@login_required
def toggle_comment(request, com_id):
    user = _get_user(request)
    comment = Comment.objects.get(pk=com_id)
    if comment.owner == user or comment.owner == None:
        comment.status = not comment.status
        comment.save()

    return httprespred(reverse('tracking:comment_detail', args=[com_id]))


#---------------------- Drawing Search ------------------------
def _pull_drawings(formdat):
    ''' Replace wildcards '*' with regex '.*'
        filter drawing names with optional qualifiers 
        return a drawing query set '''
    
    if not formdat['drawing_name']:
        return None
    # Apply drawing search qualifiers:
    #   start with simplest first, saving regex
    #   search for last - return as soon as null

    cquery = None
    # Fetch all comments that match selected comment status
    if formdat['comment_status']:
        com_stat = formdat['comment_status'] # list of selections
        if len(com_stat) > 1:   # user selected both options
            cquery = Comment.objects.prefetch_related('revision').all()
        else:                   # user selected one option
            check = {'open':True, 'closed':False}
            cquery = Comment.objects.prefetch_related('revision')\
                                    .filter(status=check[com_stat[0]])
        if not cquery.exists():
            # there are no comments (so no drawings)
            # that match the selected status
            return

    # Create a Drawing query set
    if cquery:
        # If there is a comment set, use it to filter drawings
        revs = Revision.objects.prefetch_related('drawing')\
                        .filter(pk__in=cquery.values_list('revision', flat=True))
        dquery = Drawing.objects.filter(pk__in=revs.values_list('drawing', flat=True))
    else:
        dquery = Drawing.objects

    # Filter drawings by project
    if formdat['project']:
        dquery = dquery.filter(project=formdat['project'])

    # Filter drawings based on Department name
    if formdat['department_name']:
        exp = formdat['department_name'].strip().lower().replace('*','.*')
        dquery = dquery.filter(department__name__regex=exp)

    # Filter drawings based on Block name
    if formdat['block_name']:
        exp = formdat['block_name'].strip().lower().replace('*','.*')
        blockquery = Block.objects.filter(name__regex=exp)
        dquery = dquery.filter(block__in=blockquery)

    # Filter drawings based on drawing status
    if formdat['drawing_status']:
        dquery = dquery.filter(status__status=formdat['drawing_status'])

    # Filter drawing set based on drawing name regex
    qstr = '^{}$'.format(formdat['drawing_name'].replace('*','.*'))
    dquery = dquery.filter(name__regex=qstr).order_by('name')
    return dquery


@login_required
def drawing_search(request):
    ''' Serve up drawing search form with optional qualifiers '''
    user = _get_user(request)
    drawings = False
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            drawings = _pull_drawings(form.cleaned_data)

    else:
        form = SearchForm()

    context = {'username':user, 'form':form.as_table(), 
               'drawings':drawings}
    if drawings != False:
        return render(request, 'tracking/drawing_results.html', context)
    return render(request, 'tracking/drawing_search.html', context)


#---------------------- Drawing Details ------------------------
def _get_drawing_detail(drawing_name):
    dwg = Drawing.objects.get(name=drawing_name.lower())

    dwg_attch = DrawingAttachment.objects.filter(link=dwg)
    block = Block.objects.filter(pk__in=dwg.block.values_list('id', flat=True))
    drawing = {'name':drawing_name, 'project':dwg.project, 'desc':dwg.desc,
               'phase':dwg.phase, 'block':block, 'received':dwg.received,
               'status':dwg.status, 'expected':dwg.expected,
               'department':dwg.department,  'discipline':dwg.discipline,
               'kind':dwg.kind, 'attachments':dwg_attch, 'id':dwg.id}

    revs = Revision.objects.filter(drawing=dwg).order_by('number')
    revisions = [{'id':rev.id,         'number':rev.number,
                  'date':rev.add_date, 'desc':rev.desc} for rev in revs]

    coms = Comment.objects.filter(revision__in=revs).order_by('-status')
    comments = coms

    context = {'drawing':drawing, 'revisions':revs,
               'comments':comments}
    return context


@login_required
def drawing_detail(request, drawing_name):
    ''' Fetch drawing details, and linked attachments, 
        revisions, comments, and replies'''
    user = _get_user(request)
    context = _get_drawing_detail(drawing_name)
    context['username'] = user
    return render(request, 'tracking/drawing_detail.html', context)


#----------------------  Drawing Edits ------------------------
def _update_drawing_info(drawing_name, post_info, user): 
    info = {}
    error = ''
    for key, val in post_info.items():
        if val:
            if key in ['name']:
                val = val.strip().replace(' ','-').lower()
                if not DWG_TEST.match(val):
                    error = 'Invalid character(s). Please use alphanumeric and "_ -"'
                    break
                if Drawing.objects.filter(name=val).exists():
                    error = 'Drawing already exists...'
                    break
                info[key] = val
            elif key in ['desc']:
                info[key] = val.lower()
            elif key in ['received']:
                choice = {'yes':True, 'no':False}
                info[key] = choice[val]
            elif key in ['block']:
                dwg = Drawing.objects.get(name=drawing_name)
                dwg.block.clear()
                for block in val:
                    dwg.block.add(block)
                dwg.save()
            else:
                info[key] = val
    if info and not error:
        info['mod_date'] = timezone.now()
        info['mod_by'] = user
        Drawing.objects.filter(name=drawing_name).update(**info)
        newname = None
        if 'name' in info:
            newname = info['name']
        return newname, error

    return None, error


@login_required
def drawing_edit(request, drawing_name):
    ''' Serve form to edit drawing info '''
    user = _get_user(request)
    error = None
    if request.method == 'POST':
        edit_form = DrawingAddForm(True, request.POST)
        # print(edit_form.errors)
        if edit_form.is_valid():
            if request.POST:
                post_info = edit_form.cleaned_data
                new_drawing, error = _update_drawing_info(drawing_name, post_info, user)
                if new_drawing:
                    drawing_name = new_drawing
    
    else:
        edit_form = DrawingAddForm(edit=True)

    detail = _get_drawing_detail(drawing_name)
    drawing_det = detail['drawing']
    context = {'drawing':drawing_det, 'form':edit_form, 
               'is_edit':True, 'error':error, 'username':user}
    return render(request, 'tracking/drawing_add.html', context)


#----------------------  Drawing Adds ------------------------
def _add_new_drawing(request, post_info, user):
    ''' check form data against name regex's 
        create and save new drawing '''
    error = None
    new_drawing = {}
    for key, val in post_info.items():
        if not val or key == 'block':
            continue
        if key == 'name':
            new_drawing[key] = val.strip().replace(' ','-').lower()
            if not DWG_TEST.match(new_drawing[key]):
                error = 'Invalid character(s). Please use alphanumeric and \'_, -\''
                break
            if Drawing.objects.filter(name=new_drawing[key]).exists():
                error = 'Drawing already exists...'
                break
        elif key == 'desc':
            new_drawing[key] = val.lower()
        elif key == 'received':
            choice = {'yes':True, 'no':False}
            new_drawing[key] = choice[val]
        else:
            new_drawing[key] = val

    resp = None
    if not error:
        new_drawing['add_date'] = timezone.now()
        new_drawing['mod_date'] = timezone.now()
        new_drawing['mod_by'] = user
        drawing = Drawing(**new_drawing)
        drawing.save()
        if 'block' in post_info:
            for block in post_info['block']:
                drawing.block.add(block)
            drawing.save()
        resp = httprespred(reverse('tracking:drawing_detail',
                                   args=[drawing.name]))
    return resp, error


@login_required
def drawing_add(request):
    ''' Serve form to add drawing info '''
    user = _get_user(request)
    error = None
    if request.method == 'POST':
        add_form = DrawingAddForm(False, request.POST)
        if add_form.is_valid():
            post_info = add_form.cleaned_data
            # print(post_info)
            resp, error = _add_new_drawing(request, post_info, user)
            if not error:
                return resp
   
    else:
        add_form = DrawingAddForm(edit=False)

    context = {'form':add_form, 'is_edit':False, 
               'error':error, 'username':user}
    return render(request, 'tracking/drawing_add.html', context)


#----------------------  Revision Detail ------------------------
@login_required
def revision_detail(request, drawing_name, rev_no):
    user = _get_user(request)
    dwg = Drawing.objects.get(name=drawing_name)
    revision = Revision.objects.filter(drawing=dwg).get(number=rev_no)
    comments = Comment.objects.filter(revision=revision).order_by('-status')
    attachments = RevisionAttachment.objects.filter(link=revision)
    context = {'revision':revision, 'comments':comments,
               'attachments':attachments, 'username':user}
    return render(request, 'tracking/revision_detail.html', context)


@login_required
def revision_search(request):
    # add rev search form
    pass


#----------------------  Revision Edits ------------------------
def _update_revision_info(drawing_name, rev_no, post_info, user): 
    info = {}
    error = ''
    drawing = Drawing.objects.get(name=drawing_name)
    info['drawing'] = drawing
    for key, val in post_info.items():
        if not val or key == 'drawing':
            continue

        if key == 'number':
            val = val.strip().replace(' ','-').lower()
            if not REV_TEST.match(val):
                error = 'Invalid character(s). Please use alphanumeric and \'_ . -\''
                break
            if Revision.objects.filter(number=val, drawing=drawing).exists():
                error = 'Revision already exists...'
                break
            info[key] = val
        elif key == 'desc':
            info[key] = val.lower()
        else:
            info[key] = val
    
    if info and not error:
        info['mod_date'] = timezone.now()
        info['mod_by'] = user
        Revision.objects.filter(number=rev_no, drawing=drawing).update(**info)
        new_rev = None
        if 'number' in info:
            new_rev = info['number']
        return new_rev, drawing, error

    return None, None, error


@login_required
def revision_edit(request, drawing_name, rev_no):
    user = _get_user(request)

    error = None
    dwg = None
    if request.method == 'POST':
        edit_form = RevisionAddForm(None, True, request.POST)
        if edit_form.is_valid():
            post_info = edit_form.cleaned_data
            new_rev, dwg, error = _update_revision_info(drawing_name, rev_no,
                                                        post_info, user)
            if new_rev:
                rev_no = new_rev

    else:
        edit_form = RevisionAddForm(drawing_name=drawing_name, edit=True)

    if not dwg:
        dwg = Drawing.objects.get(name=drawing_name)
    revision = Revision.objects.filter(drawing=dwg).get(number=rev_no)
    context = {'drawing':dwg, 'revision':revision, 'form':edit_form, 
               'is_edit':True, 'error':error, 'username':user}
    return render(request, 'tracking/revision_add.html', context)


#----------------------  Revision Adds ------------------------
@login_required
def drawing_revision_add(request, drawing_name):
    ''' Serve add revision form with current drawing 
        info already filled out. Form should redirect 
        to 'tracking:revision_add' for processing '''
    user = _get_user(request)
    error = None

    add_form = RevisionAddForm(drawing_name=drawing_name, edit=False)
    drawing = Drawing.objects.get(name=drawing_name)
    context = {'form':add_form, 'drawing':drawing, 'is_edit':False, 
               'error':error, 'username':user}
    return render(request, 'tracking/revision_add.html', context)


def _add_new_revision(request, post_info, user):
    ''' check form data against name regex's 
        create and save new drawing '''
    error = None
    new_rev = {}
    for key, val in post_info.items():
        if not val:
            continue
        if key == 'number':
            new_rev[key] = val.strip().replace(' ','-').lower()
            if not REV_TEST.match(new_rev[key]):
                error = 'Invalid character(s). Please use alphanumeric and \'_ . -\''
                break
            if Revision.objects.filter(number=new_rev[key],
                                       drawing=post_info['drawing']).exists():
                error = 'Drawing already exists...'
                break
        elif key == 'desc':
            new_rev[key] = val.lower()
        elif key == 'add_date':
            if not val:
                new_rev[key] = timezone.now()
            else:
                new_rev[key] = val
        else:
            new_rev[key] = val

    resp = None
    if not error:
        new_rev['mod_date'] = timezone.now()
        new_rev['mod_by'] = user
        revision = Revision(**new_rev)
        revision.save()
        resp = httprespred(reverse('tracking:revision_detail',
                                   args=[revision.drawing.name,
                                         revision.number]))
    return resp, error


@login_required
def revision_add(request):
    user = _get_user(request)
    error = None
    if request.method == 'POST':
        add_form = RevisionAddForm(None, False, request.POST)
        if add_form.is_valid():
            post_info = add_form.cleaned_data
            resp, error = _add_new_revision(request, post_info, user)
            if not error:
                return resp
        else:
            error = '''Missing Requried Fields.
                       Return to prev. page for drawing field to re-filter'''
    else:
        add_form = RevisionAddForm(drawing_name=None, edit=False)

    context = {'form':add_form, 'drawing':None, 'is_edit':False, 
               'error':error, 'username':user}
    return render(request, 'tracking/revision_add.html', context)


#----------------------  Comment Detail ------------------------
@login_required
def comment_detail(request, com_id):
    user = _get_user(request)
    com = Comment.objects.prefetch_related('revision')\
                         .filter(pk=com_id)
    comment = com.first()
    com_attch = CommentAttachment.objects.filter(link=comment)
    revs = [rev for rev in comment.revision.all()]
 
    reps = Reply.objects.filter(comment=comment).order_by('number')
    replies = [{'reply':rep, 'attachments':ReplyAttachment.objects.filter(link=rep)} for rep in reps]

    context = {'comment':comment, 'replies':replies,
               'com_attachments':com_attch, 'revisions':revs, 'username':user}
    return render(request, 'tracking/comment_detail.html', context)


#----------------------  Comment Add, Edit ------------------------
@login_required
def drawing_comment_add(request, drawing_name):
    user = _get_user(request) 
    
    error = None
    if request.method == 'POST':
        add_form = CommentAddForm(drawing_name, False, request.POST )
        if add_form.is_valid():
            post_info = add_form.cleaned_data
            resp, error  = _add_new_comment(request, post_info, user)
            if not error:
                return resp

    add_form = CommentAddForm(drawing_name=drawing_name, edit=False)

    drawing = Drawing.objects.get(name=drawing_name)
    revisions = Revision.objects.filter(drawing=drawing)
    if not revisions:
        error = 'Please add a revision to comment on'

    context = {'username':user, 'drawing':drawing,
               'revisions':revisions, 'form':add_form, 'error':error}
    return render(request, 'tracking/comment_add.html', context)


def _add_new_comment(request, post_info, user):
    ''' check form data create and save new comment '''
    error = None
    new_com = {}
    for key, val in post_info.items():
        if not val:
            continue
        if key == 'status':
            stat = {'open':True, 'closed':False, '':True}
            new_com['status'] = stat[val]
        elif key == 'desc':
            new_com[key] = val.lower()
        elif key == 'revision':
            revs = val
        else:
            new_com[key] = val

    resp = None
    if not error:
        new_com['mod_date'] = timezone.now()
        new_com['mod_by'] = user
        new_com['owner'] = user
        comment = Comment(**new_com)
        comment.save()
        for rev in revs:
            comment.revision.add(rev)
            comment.save()

        resp = httprespred(reverse('tracking:comment_detail',
                                   args=[comment.id]))
    return resp, error


def _update_comment_info(com_id, post_info, user):
    info = {}
    error = None

    for key, val in post_info.items():
        if not val:
            continue
        if key == 'status':
            stat = {'open':True, 'closed':False, '':True}
            info['status'] = stat[val]
        elif key == 'desc':
            info[key] = val.lower()
        elif key == 'revision':
            com = Comment.objects.get(pk=com_id)
            com.revision.clear()
            for rev in val:
                com.revision.add(rev)
            com.save()
        else:
            info[key] = val

    comment = Comment.objects.filter(pk=com_id)
    resp = None
    if not error:
        info['mod_date'] = timezone.now()
        info['mod_by'] = user
        comment.update(**info)

    return comment.first(), error


@login_required
def comment_edit(request, com_id):
    user = _get_user(request)

    error = None
    comment = None
    if request.method == 'POST':
        edit_form = CommentAddForm(None, True, request.POST)
        if edit_form.is_valid():
            post_info = edit_form.cleaned_data
            comment, error = _update_comment_info(com_id,
                                               post_info, user)

    else:
        edit_form = CommentAddForm(drawing_name=None, edit=True)

    if not comment:
        comment = Comment.objects.get(pk=com_id)
    context = {'username':user, 'comment':comment, 'revisions':comment.revision.all(),
               'is_edit':True, 'form':edit_form, 'error':error}
    return render(request, 'tracking/comment_add.html', context)


#---------------------  Reply Detail ------------------------
@login_required
def reply_detail(request, com_id, rep_no):
    user = _get_user(request)
    error = None
    comment = Comment.objects.get(pk=com_id)
    reply = Reply.objects.filter(comment=comment, number=rep_no).first()
    rep_attch = ReplyAttachment.objects.filter(link=reply)
    context = {'comment':comment, 'reply':reply,
               'rep_attachments':rep_attch, 'error':error, 'username':user}
    return render(request, 'tracking/reply_detail.html', context)


@login_required
def comment_reply_add(request, com_id):    
    user = _get_user(request) 
    error = None
    if request.method == 'POST':
        add_form = ReplyAddForm(False, request.POST )
        if add_form.is_valid():
            post_info = add_form.cleaned_data
            resp, error  = _add_new_reply(request, post_info, user, com_id)
            if not error:
                return resp

    add_form = ReplyAddForm(edit=False)

    comment = Comment.objects.get(pk=com_id)
    reply = None
    context = {'username':user, 'comment':comment,
               'reply':reply, 'form':add_form, 'error':error}
    return render(request, 'tracking/reply_add.html', context)


def _add_new_reply(request, post_info, user, com_id):
    ''' check form data, create and save new reply '''
    error = None
    new_rep = {}
    for key, val in post_info.items():
        if not val:
            continue
        else:
            new_rep[key] = val

    if not new_rep:
        return None, 'Please fill all fields'

    resp = None
    comment = Comment.objects.get(pk=com_id)
    if not error:
        new_rep['number'] = comment.number_replies() + 1
        new_rep['comment'] = comment
        new_rep['mod_date'] = timezone.now()
        new_rep['mod_by'] = user
        new_rep['owner'] = user
        reply = Reply(**new_rep)
        reply.save()

        resp = httprespred(reverse('tracking:reply_detail',
                                   args=[comment.id, new_rep['number']]))
    return resp, error


@login_required
def reply_edit(request, com_id, rep_no):
    user = _get_user(request)

    error = None
    reply = None
    comment = None
    if request.method == 'POST':
        edit_form = ReplyAddForm(True, request.POST)
        if edit_form.is_valid():
            post_info = edit_form.cleaned_data
            reply, comment, error = _update_reply_info(com_id, rep_no,
                                               post_info, user)

    edit_form = ReplyAddForm(edit=True)

    if not comment:
        comment = Comment.objects.get(pk=com_id)

    if not reply:
        reply = Reply.objects.filter(comment=comment, number=rep_no).first()

    context = {'username':user, 'comment':comment, 'reply':reply,
               'is_edit':True, 'form':edit_form, 'error':error}
    return render(request, 'tracking/reply_add.html', context)


def _update_reply_info(com_id, rep_no, post_info, user):
    info = {}
    error = None
    comment = Comment.objects.get(pk=com_id)
    for key, val in post_info.items():
        if not val:
            continue
        else:
            info[key] = val

    comment = Comment.objects.get(pk=com_id)
    reply = Reply.objects.filter(comment=comment, number=rep_no)
    if not error:
        info['mod_date'] = timezone.now()
        info['mod_by'] = user
        reply.update(**info)

    return reply.first(), comment, error


#----------------------  Attachments Add, Serve, Remove ------------------------
def _store_attch(request, item_type, item_id, user):
    ''' store upload to correct table specified by item_type '''
    attch = {'drawing':DrawingAttachment, 'revision':RevisionAttachment,
             'comment':CommentAttachment, 'reply':ReplyAttachment}
    table = {'drawing':Drawing, 'revision':Revision,
             'comment':Comment, 'reply':Reply}
    detail = {'drawing':'tracking:drawing_detail', 'revision':'tracking:revision_detail',
             'comment':'tracking:comment_detail', 'reply':'tracking:reply_detail'}
    obj = table[item_type].objects.get(pk=item_id)
    newfile = attch[item_type](upload=request.FILES['newfile'],
                               link=obj,
                               mod_by=user)
    # print(newfile.upload.name)
    # print(newfile.filename())
    # print(newfile.link)
    # print(newfile.mod_by)
    newfile.save()
    args = { 'drawing':[obj.name]        if item_type == 'drawing' else None, 
            'revision':[obj.drawing.name, 
                        obj.number]      if item_type == 'revision' else None,
             'comment':[obj.id]          if item_type == 'comment' else None, 
               'reply':[obj.comment.id,
                        obj.number]      if item_type == 'reply' else None}
    return httprespred(reverse(detail[item_type],
                           args=args[item_type]))


@login_required
def add_attachment(request, item_type, item_id):
    user = _get_user(request)
    error = None
    if request.method == 'POST':
        file_form = FileForm(request.POST, request.FILES)
        if file_form.is_valid():
            if 'newfile' in request.FILES:
                if request.FILES['newfile']._size > 10 * 1024 * 1024: # size > 10mb
                    error = 'File too large. Please keey it under 10mb'
                else:
                    return _store_attch(request, item_type, item_id, user)
        # else:
        #     print('form not valid')

    file_form = FileForm()

    context = {'form':file_form, 'item':{'type':item_type, 'id':item_id},
               'username':user, 'error':error}
    return render(request, 'tracking/attachment_add.html', context)


def _remove_attch(request, item_type, item_id, info):
    ''' remove & delete specified uploaded attachments '''
    attch = {'drawing':DrawingAttachment, 'revision':RevisionAttachment,
             'comment':CommentAttachment, 'reply':ReplyAttachment}
    table = {'drawing':Drawing, 'revision':Revision,
             'comment':Comment, 'reply':Reply}
    detail = {'drawing':'tracking:drawing_detail', 'revision':'tracking:revision_detail',
             'comment':'tracking:comment_detail', 'reply':'tracking:reply_detail'}
    obj = table[item_type].objects.get(pk=item_id)
    
    for f in info['files']:
        filepath = f.upload.name
        f.delete()
        os.remove(os.path.join(settings.MEDIA_ROOT, filepath))
        base = os.path.dirname(os.path.join(settings.MEDIA_ROOT, filepath))
        if not os.listdir(base):
            os.rmdir(base)

    args = { 'drawing':[obj.name]        if item_type == 'drawing' else None, 
            'revision':[obj.drawing.name, 
                        obj.number]      if item_type == 'revision' else None,
             'comment':[obj.id]          if item_type == 'comment' else None, 
               'reply':[obj.comment.id,
                        obj.number]      if item_type == 'reply' else None}
    return httprespred(reverse(detail[item_type],
                           args=args[item_type]))


@login_required
def remove_attachment(request, item_type, item_id):
    user = _get_user(request)
    if request.method == 'POST':
        remove_file_form = RemoveFileForm(item_type, item_id, request.POST, request.FILES)
        if remove_file_form.is_valid():
            info = remove_file_form.cleaned_data
            return _remove_attch(request, item_type, item_id, info)
        # else:
        #     print('form not valid')

    remove_file_form = RemoveFileForm(item_type, item_id)

    context = {'form':remove_file_form, 'item':{'type':item_type, 'id':item_id}, 'username':user}
    return render(request, 'tracking/attachment_remove.html', context)


@login_required
def serve_attachment(request, file_type, file_id):
    ''' Serve attachment for viewing or download '''
    attch = {'drawing':DrawingAttachment, 'revision':RevisionAttachment,
             'comment':CommentAttachment, 'reply':ReplyAttachment}
    try:
        attachment = attch[file_type].objects.get(pk=file_id)
        filepath = attachment.upload.name
        filename = attachment.filename(filepath=filepath)
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)
        with open(full_path, 'rb') as attch:
            response = httpresp(attch.read(), content_type=mimetypes.guess_type(full_path)[0])
            response['Content-Disposition'] = 'filename={}'.format(filename)
            return response

    except Exception as ex:
        return httpresp('''Error: {} <br/>
                        Unable to serve file:  file_id: {}
                        </br>Please notify James Kominick
                        </br>Close this tab'''\
                        .format(ex, file_id))

