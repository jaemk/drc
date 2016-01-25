import os
import mimetypes

from django.shortcuts import render
from django.shortcuts import get_object_or_404 as get_or_404

from django.http import HttpResponse as httpresp
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from django.conf import settings

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


def _get_username(request):
    ''' Helper to return user from a request '''
    if request.user.is_authenticated():
        username = request.user
    else:
        username = None

    return username


def logout_view(request):
    ''' Logout confirmation '''
    username = request.user
    logout(request)
    return httpresp('''Goodbye {} !<br>
                    You\'ve successfully logged out!<br>
                    <a href="/">return to homepage</a>'''.format(username))


@login_required
def index(request):
    ''' Homepage '''
    username = _get_username(request)
    return render(request, 'tracking/index.html', {'username':username})


### Drawing Search ###
def _pull_drawings(formdat):
    ''' Replace wildcards '*' with regex '.*'
        filter drawing names with optional qualifiers '''
    if not formdat['drawing_name']:
        return None
    # apply other qualifiers
    # start with simplest first, saving refex
    # search for last - return as soon as null
    cquery = None
    if formdat['comment_status']:
        com_stat = formdat['comment_status']
        if len(com_stat) > 1: # user selected both options
            cquery = Comment.objects.prefetch_related('revision').all()
        else: # user selected one option
            check = {'open':True, 'closed':False}
            cquery = Comment.objects.prefetch_related('revision')\
                                    .filter(status=check[com_stat[0]])
        if not cquery.exists():
            return

    if cquery:
        revs = Revision.objects.prefetch_related('drawing')\
                        .filter(pk__in=cquery.values_list('revision', flat=True))
        dquery = Drawing.objects.filter(pk__in=revs.values_list('drawing', flat=True))

    else:
        dquery = Drawing.objects

    if formdat['department_name']:
        exp = formdat['department_name'].strip().lower().replace('*','.*')
        dquery = dquery.filter(department__name__regex=exp)

    if formdat['block_name']:
        exp = formdat['block_name'].strip().lower().replace('*','.*')
        blockquery = Block.objects.filter(name__regex=exp)
        dquery = dquery.filter(block__in=blockquery)

    if formdat['drawing_status']:
        dquery = dquery.filter(status__status=formdat['drawing_status'])


    qstr = '^{}$'.format(formdat['drawing_name'].replace('*','.*'))
    dquery = dquery.filter(name__regex=qstr).order_by('name')
    return dquery


@login_required
def drawing_search(request):
    ''' Serve up drawing search form with optional qualifiers '''
    username = _get_username(request)
    drawings = False
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            drawings = _pull_drawings(form.cleaned_data)

    else:
        form = SearchForm()

    context = {'username':username, 'form':form.as_table(), 
               'drawings':drawings}
    if drawings != False:
        return render(request, 'tracking/drawing_results.html', context)
    return render(request, 'tracking/drawing_search.html', context)


def _get_drawing_detail(drawing_name):
    dwg = Drawing.objects.get(name=drawing_name.lower())

    dwg_attch = DrawingAttachment.objects.filter(drawing=dwg)
    block = Block.objects.filter(pk__in=dwg.block.values_list('id', flat=True))
    drawing = {'name':drawing_name, 'project':dwg.project, 'desc':dwg.desc,
               'phase':dwg.phase, 'block':block, 'received':dwg.received,
               'status':dwg.status, 'expected':dwg.expected,
               'department':dwg.department,  'discipline':dwg.discipline,
               'kind':dwg.kind, 'attachments':dwg_attch, 'id':dwg.id}

    revs = Revision.objects.filter(drawing=dwg)
    revisions = [{'id':rev.id,         'number':rev.number,
                  'date':rev.add_date, 'desc':rev.desc} for rev in revs]

    coms = Comment.objects.filter(revision__in=revs)
    comments = coms

    context = {'drawing':drawing, 'revisions':revs,
               'comments':comments}
    return context


@login_required
def drawing_detail(request, drawing_name):
    ''' Fetch drawing details, and linked attachments, 
        revisions, comments, and replies'''
    username = _get_username(request)
    context = _get_drawing_detail(drawing_name)
    context['username'] = username
    return render(request, 'tracking/drawing_detail.html', context)


@login_required
def drawing_edit(request, drawing_name):
    ''' Serve form to edit drawing info or add attachments '''
    username = _get_username(request)
    if request.method == 'POST':
        edit_form = DrawingAddForm(True, request.POST)
        print(edit_form.errors)
        if edit_form.is_valid():
            if request.POST:
                #post_info = 
                return httpresp('{} - {}'.format(request.POST['name'], request.POST['received']))
                
            return httprespred(reverse('tracking:drawing_detail', args=[drawing_name]))
        # else:
        #     return httpresp( 'Form was not valid.')     
    else:
        edit_form = DrawingAddForm(edit=True)

    detail = _get_drawing_detail(drawing_name)
    drawing_det = detail['drawing']
    context = {'drawing':drawing_det, 'form':edit_form, 'is_edit':True}
    return render(request, 'tracking/drawing_add.html', context)


@login_required
def revision_search(request):
    # add rev search form
    pass

@login_required
def revision_detail(request, drawing_name, rev_no):
    dwg = Drawing.objects.get(name=drawing_name)
    revision = Revision.objects.filter(drawing=dwg).get(number=rev_no)
    comments = Comment.objects.filter(revision=revision)
    attachments = RevisionAttachment.objects.filter(revision=revision)
    context = {'revision':revision, 'comments':comments, 'attachments':attachments}
    return render(request, 'tracking/revision_detail.html', context)


@login_required
def comment_detail(request, com_id):
    com = Comment.objects.prefetch_related('revision')\
                         .filter(pk=com_id)
    comment = com.first()
    com_attch = CommentAttachment.objects.filter(comment=comment)
    revs = [rev for rev in comment.revision.all()]
    # revs = Revision.objects.prefetch_related('drawing')\
    #             .filter(pk__in=com.values_list('revision', flat=True))
    # dwgs = Drawing.objects.filter(pk__in=revs.values_list('drawing', flat=True))
    
    reps = Reply.objects.filter(comment=comment).order_by('number')
    replies = [{'reply':rep, 'attachments':ReplyAttachment.objects.filter(reply=rep)} for rep in reps]

    context = {'comment':comment, 'replies':replies,
               'com_attachments':com_attch, 'revisions':revs}
               #  'revisions':revs,
               # 'drawings':dwgs, 'attachments':attachments}
    return render(request, 'tracking/comment_detail.html', context)


@login_required
def reply_detail(request, com_id, rep_id):
    return httpresp('reply: {} on com: {}'.format(rep_id, com_id))


def _store_attch(request, item_type, item_id, username):
    # need to check item_type to query the right table
    if item_type == 'drawing':
        drawing = Drawing.objects.get(pk=item_id)
        newfile = DrawingAttachment(upload=request.FILES['newfile'],
                                    drawing=drawing,
                                    mod_by=username)
        newfile.save()
        return httprespred(reverse('tracking:drawing_detail',
                           args=[drawing.name]))
    elif item_type == 'revision':
        revision = Revision.objects.get(pk=item_id)
        newfile = RevisionAttachment(upload=request.FILES['newfile'],
                                     revision=revision,
                                     mod_by=username)
        newfile.save()
        return httprespred(reverse('tracking:revision_detail',
                           args=[revision.drawing.name, revision.number]))
    elif item_type == 'comment':
        comment = Comment.objects.get(pk=item_id)
        newfile = CommentAttachment(upload=request.FILES['newfile'],
                                    comment=comment,
                                    mod_by=username)
        newfile.save()
        return httprespred(reverse('tracking:comment_detail',
                           args=[comment.id]))
    elif item_type == 'reply':
        reply = Reply.objects.get(pk=item_id)
        newfile = ReplyAttachment(upload=request.FILES['newfile'],
                                  reply=reply,
                                  mod_by=username)
        newfile.save()
        return httprespred(reverse('tracking:reply_detail',
                           args=[reply.comment.id, reply.id]))
    
@login_required
def add_attachment(request, item_type, item_id):
    username = _get_username(request)
    if request.method == 'POST':
        file_form = FileForm(request.POST, request.FILES)
        if file_form.is_valid():
            if 'newfile' in request.FILES:
                if request.FILES['newfile']._size > 10 * 1024 * 1024: # size > 10mb
                    error = 'File too large. Please keey it under 10mb'
                else:
                    return _store_attch(request, item_type, item_id, username)

        else:
            print('form not valid')

    file_form = FileForm()

    context = {'form':file_form, 'item':{'type':item_type, 'id':item_id}, 'username':username}
    return render(request, 'tracking/attachment_add.html', context)


@login_required
def serve_attachment(request, file_type, file_id):
    ''' Serve attachment for viewing or download '''
    attch = {'drawing':DrawingAttachment, 'revision':RevisionAttachment,
             'comment':CommentAttachment, 'repy':ReplyAttachment}
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
                        </br><a href="javascript:history.go(-1);">Return to prev</a>'''\
                        .format(ex, file_id))


@login_required
def open_comment_search(request):
    coms = Comment.objects.prefetch_related('revision')\
                         .filter(status=True)
    context = {'comments':coms}
    return render(request, 'tracking/open_comments.html', context)


@login_required
def toggle_comment(request, com_id):
    user = _get_username(request)
    comment = Comment.objects.get(pk=com_id)
    if comment.owner == user or comment.owner == None:
        comment.status = not comment.status
        comment.save()

    return httprespred(reverse('tracking:comment_detail', args=[com_id]))
    
