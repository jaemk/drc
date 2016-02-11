from django.shortcuts import render
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from tracking.models import Drawing
from tracking.models import Revision
from tracking.models import Comment
from tracking.models import CommentAttachment
from tracking.models import Reply
from tracking.models import ReplyAttachment

from tracking.forms import CommentAddForm

from .subscriptions import _update_subscriptions


#----------------------  Comment Detail ------------------------
@login_required
def comment_detail(request, com_id):
    user = request.user
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
    user = request.user 
    
    error = None
    if request.method == 'POST':
        add_form = CommentAddForm(drawing_name, False, request.POST )
        if add_form.is_valid():
            post_info = add_form.cleaned_data
            resp, error  = _add_new_comment(request, post_info, user)
            if not error:
                return resp

    else:
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

        _update_subscriptions(drawing=revs[0].drawing, mod_date=new_com['mod_date'],
                              mod_by=new_com['mod_by'],
                              mod_info='new comment({}) on {}'.format(comment.id,
                                                                      revs[0]))
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
        rev = comment.first().revision.first()
        _update_subscriptions(drawing=rev.drawing, mod_date=info['mod_date'],
                              mod_by=info['mod_by'],
                              mod_info='edit comment({}) on {}'.format(comment.first().id,
                                                                       rev))

    return comment.first(), error


@login_required
def comment_edit(request, com_id):
    user = request.user

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
