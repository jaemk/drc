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
from .models import Comment
from .models import Reply

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
    attch_names, attch_ids = dwg.get_attachment_names_ids()
    dwg_attch = [{'name':attch_names[i], 'id':attch_ids[i]} for i in range(len(attch_names))]
    drawing = {'name':drawing_name, 'project':dwg.project, 'desc':dwg.desc,
               'phase':dwg.phase, 'block':dwg.block, 'received':dwg.received,
               'status':dwg.status, 'expected':dwg.expected,
               'department':dwg.department,  'discipline':dwg.discipline,
               'kind':dwg.kind,       'attachments':dwg_attch}

    revs = Revision.objects.filter(drawing=dwg)
    revisions = [{'id':rev.id,         'number':rev.number,
                  'date':rev.add_date, 'desc':rev.desc} for rev in revs]

    coms = Comment.objects.filter(revision__in=revs)
    comments = [{'id':com.id,         'status':com.status,
                 'date':com.add_date, 'owner':com.owner} for com in coms]

    context = {'drawing':drawing, 'revisions':revs, 'comments':comments}
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
    errors = None
    if request.method == 'POST':
        #drawing_form = DrawingForm() # want to initialize with current info and use drawing_form instead
        edit_form = DrawingAddForm(request.POST, request.FILES)
        # print(request.FILES['newfile'].__dict__)
        if edit_form.is_valid():
            if 'newfille' in request.FILES:
                if request.FILES['newfile']._size > 10 * 1024 * 1024:
                    # size > 10mb
                    error = 'File too large. Please keey it under 10mb'
                else:
                    drawing = Drawing.objects.get(name=drawing_name.lower())
                    newfile = DrawingAttachment(upload=request.FILES['newfile'],
                                                drawing=drawing,
                                                mod_by=username)
                    newfile.save()

            return httprespred(reverse('tracking:drawing_detail', args=[drawing_name]))
    else:
        detail = _get_drawing_detail(drawing_name)
        drawing = detail['drawing']
        current = {'name':drawing['name'], 'desc':drawing['desc']}
        edit_form = DrawingAddForm(initial=current)
        # file_form = FileForm()

    info = Drawing.objects.get(name=drawing_name.lower())
    drawing = {'name':info.name}
    context = {'drawing':drawing, 'form':edit_form, 'errors':errors}
    return render(request, 'tracking/drawing_add.html', context)


@login_required
def revision_search(request):
    # add rev search form
    pass

@login_required
def revision_detail(request, drawing_name, rev_no):
    return httpresp('Revision detail for rev: {} on drawing: {}'\
                    .format(rev_no, drawing_name))

@login_required
def comment_detail(request, com_id):
    com = Comment.objects.prefetch_related('revision')\
                         .filter(pk=com_id)
    revs = Revision.objects.prefetch_related('drawing')\
                .filter(pk__in=com.values_list('revision', flat=True))
    dwgs = Drawing.objects.filter(pk__in=revs.values_list('drawing', flat=True))
    return httpresp('''Comment detail id: {}<br/>
                       made on revs: {}<br/>
                       rev-dwgs: {}'''.format(com_id, 
                                              ', '.join([r.number for r in revs]),
                                              ', '.join([d.name for d in dwgs])))

@login_required
def attachment_edit(request, drc_type, identifier):
    # move the drawing_edit functionality here 
    pass

@login_required
def serve_attachment(request, drawing_name=None, file_id=None):
    ''' Serve attachment for viewing or download '''
    try:
        attachment = DrawingAttachment.objects.get(pk=file_id)
        filepath = attachment.upload.name
        filename = attachment.filename(filepath=filepath)
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)
        with open(full_path, 'rb') as attch:
            response = httpresp(attch.read(), content_type=mimetypes.guess_type(full_path)[0])
            response['Content-Disposition'] = 'filename={}'.format(filename)
            return response

    except Exception as ex:
        return httpresp('''Error: {} <br/>
                        Unable to serve drawing: {}, file_id: {}
                        </br>Please notify James Kominick
                        </br><a href="javascript:history.go(-1);">Return to prev</a>'''\
                        .format(ex, drawing_name, file_id))


@login_required
def open_comment_search(request):
    com = Comment.objects.prefetch_related('revision')\
                         .filter(status=True)
    if not com:
        context = {'no_comments':'No open comments'}
        return httpresp('no open comments')
    return httpresp(com)
    # query sets are being evaluated
    # revs = Revision.objects.filter(pk__in=com[:1].values_list('revision',
    #                                                        flat=True))
    # comments = [{'id':com[0].id, 'desc':com[0].desc, 'text':com[0].text,
    #              'status':com[0].status, 'owner':com[0].owner, 'revs':revs}]
    # if com[1:]:
    #     for i in range(len(com[1:])):
    #         newcom = com[i+1:]
    #         revs = Revision.objects.filter(pk__in=newcom[:1].values_list('revision',
    #                                                        flat=True))
    #         comments.append({'id':newcom[:1].id, 'desc':newcom[:1].desc, 'text':newcom[:1].text,
    #              'status':newcom[:1].status, 'owner':newcom[:1].owner, 'revs':revs})
    # return httpresp(comments)
