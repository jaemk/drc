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


def _get_username(request):
    ''' Helper to return user from a request '''
    if request.user.is_authenticated():
        username = request.user
    else:
        username = None

    return username


def logout_view(request):
    username = request.user
    logout(request)
    return httpresp('''Goodbye {} !<br>
                    You\'ve successfully logged out!<br>
                    <a href="/">return to homepage</a>'''.format(username))


@login_required(login_url='/accounts/login')
def index(request):
    username = _get_username(request)
    return render(request, 'tracking/index.html', {'username':username})


### Drawing Search ###
def _pull_drawings(formdat):
    if not formdat['drawing_name']:
        return None
    qstr = '^{}$'.format(formdat['drawing_name'].replace('*','.*'))
    dquery = Drawing.objects.filter(name__regex=qstr)
    return dquery

@login_required(login_url='/accounts/login')
def drawing_search(request):
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


@login_required(login_url='/accounts/login')
def drawing_detail(request, drawing_name):
    username = _get_username(request)
    info = Drawing.objects.get(name=drawing_name.lower())
    attch_names, attch_ids = info.get_attachment_names_ids()
    attch = [{'name':attch_names[i], 'id':attch_ids[i]} for i in range(len(attch_names))]
    drawing = {'name':drawing_name, 'desc':info.desc, 'phase':info.phase,
               'received':info.received, 'status':info.status.status,
               'expected':info.expected, 'dep':info.department.name,
               'disc':info.discipline.name, 'kind':info.kind.name,
               'attachments':attch}

    context = {'username':username, 'drawing':drawing}
    return render(request, 'tracking/drawing_detail.html', context)


@login_required(login_url='/accounts/login')
def drawing_edit(request, drawing_name):
    username = _get_username(request)
    errors = None
    if request.method == 'POST':
        #drawing_form = DrawingForm() # want to initialize with current info and use drawing_form instead
        file_form = FileForm(request.POST, request.FILES)
        print(request.FILES['newfile'].__dict__)
        if file_form.is_valid():
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
        file_form = FileForm()

    info = Drawing.objects.get(name=drawing_name.lower())
    drawing = {'name':info.name}
    context = {'drawing':drawing, 'form':file_form, 'errors':errors}
    return render(request, 'tracking/drawing_add.html', context)


@login_required(login_url='/accounts/login')
def attachment(request, drawing_name, file_id):
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
