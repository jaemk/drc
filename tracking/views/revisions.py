import re

from django.shortcuts import render
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from tracking.models import Drawing
from tracking.models import Revision
from tracking.models import RevisionAttachment
from tracking.models import Comment

from tracking.forms import RevisionAddForm

from .subscriptions import _update_subscriptions


REV_TEST = re.compile('^([a-zA-Z0-9_\.-]+)$')


#----------------------  Revision Detail ------------------------
@login_required
def revision_detail(request, drawing_name, rev_no):
    user = request.user
    dwg = Drawing.objects.get(name=drawing_name)
    revision = Revision.objects.filter(drawing=dwg).get(number=rev_no)
    comments = Comment.objects.filter(revision=revision).order_by('-status')
    attachments = RevisionAttachment.objects.filter(link=revision)
    context = {'revision':revision, 'comments':comments,
               'attachments':attachments, 'username':user}
    return render(request, 'tracking/revision_detail.html', context)


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
            rev_no = new_rev

        _update_subscriptions(drawing=drawing, mod_date=info['mod_date'],
                              mod_by=info['mod_by'],
                              mod_info='edit rev {}-{}'.format(drawing_name.upper(), rev_no))
        return new_rev, drawing, error

    return None, None, error


@login_required
def revision_edit(request, drawing_name, rev_no):
    user = request.user

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
    user = request.user
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
                error = 'Revision already exists...'
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
        _update_subscriptions(drawing=revision.drawing, mod_date=new_rev['mod_date'],
                              mod_by=new_rev['mod_by'],
                              mod_info='new rev {}-{}'.format(revision.drawing.name.upper(),
                                                              revision.number.upper()))
        resp = httprespred(reverse('tracking:revision_detail',
                                   args=[revision.drawing.name,
                                         revision.number]))
    return resp, error


@login_required
def revision_add(request):
    user = request.user
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
                       Return to previous page for drawing field to re-auto-filter'''
    else:
        add_form = RevisionAddForm(drawing_name=None, edit=False)

    context = {'form':add_form, 'drawing':None, 'is_edit':False, 
               'error':error, 'username':user}
    return render(request, 'tracking/revision_add.html', context)

