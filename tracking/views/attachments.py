import os
import mimetypes

from django.shortcuts import render
from django.http import HttpResponse as httpresp
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from django.conf import settings

from tracking.models import Drawing
from tracking.models import DrawingAttachment
from tracking.models import Revision
from tracking.models import RevisionAttachment
from tracking.models import Comment
from tracking.models import CommentAttachment
from tracking.models import Reply
from tracking.models import ReplyAttachment

from tracking.forms import FileForm
from tracking.forms import RemoveFileForm


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
    user = request.user
    error = None
    if request.method == 'POST':
        file_form = FileForm(request.POST, request.FILES)
        if file_form.is_valid():
            if 'newfile' in request.FILES:
                if request.FILES['newfile']._size > 5 * 1024 * 1024: # size > 5mb
                    error = 'File too large. Please keey it under 5mb'
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
    user = request.user
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

