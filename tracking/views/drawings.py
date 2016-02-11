import re

from django.shortcuts import render
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from tracking.models import Block
from tracking.models import Drawing
from tracking.models import DrawingAttachment
from tracking.models import DrawingSubscription
from tracking.models import Revision
from tracking.models import Comment

from tracking.forms import DrawingAddForm

from .subscriptions import _update_subscriptions


DWG_TEST = re.compile('^([a-zA-Z0-9_-]+)$')


#---------------------- Drawing Details ------------------------
def _get_drawing_detail(drawing_name):
    dwg = Drawing.objects.get(name=drawing_name.lower())

    dwg_attch = DrawingAttachment.objects.filter(link=dwg)
    block = Block.objects.filter(pk__in=dwg.block.values_list('id', flat=True))
    drawing = {'name':drawing_name, 'project':dwg.project, 'desc':dwg.desc,
               'phase':dwg.phase, 'block':block, 'received':dwg.received,
               'status':dwg.status, 'expected':dwg.expected,
               'department':dwg.department,  'discipline':dwg.discipline,
               'kind':dwg.kind, 'attachments':dwg_attch, 'id':dwg.id, 'dwg':dwg}

    revs = Revision.objects.filter(drawing=dwg).order_by('number')
    revisions = [{'id':rev.id,         'number':rev.number,
                  'date':rev.add_date, 'desc':rev.desc} for rev in revs]

    coms = Comment.objects.filter(revision__in=revs).order_by('-status','id')\
                                                    .distinct()
    comments = coms

    context = {'drawing':drawing, 'revisions':revs,
               'comments':comments}
    return context


def _check_subscription(user, drawing):
    return DrawingSubscription.objects.filter(drawing=drawing, user=user).exists()


@login_required
def drawing_detail(request, drawing_name):
    ''' Fetch drawing details, and linked attachments, 
        revisions, comments, and replies'''
    user = request.user
    context = _get_drawing_detail(drawing_name)
    context['subscribed'] = _check_subscription(user, context['drawing']['dwg'])
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
            drawing_name = newname
        _update_subscriptions(drawing_name=drawing_name, mod_date=info['mod_date'],
                              mod_by=info['mod_by'], mod_info='edit drawing {}'.format(drawing_name.upper()))
        return newname, error

    return None, error


@login_required
def drawing_edit(request, drawing_name):
    ''' Serve form to edit drawing info '''
    user = request.user
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
    user = request.user
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
