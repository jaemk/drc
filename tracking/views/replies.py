from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from tracking.models import Comment
from tracking.models import Reply
from tracking.models import ReplyAttachment

from tracking.forms import ReplyAddForm

from .subscriptions import _update_subscriptions


#---------------------  Reply Detail ------------------------
@login_required
def reply_detail(request, com_id, rep_no):
    user = request.user
    error = None
    comment = Comment.objects.get(pk=com_id)
    reply = Reply.objects.filter(comment=comment, number=rep_no).first()
    rep_attch = ReplyAttachment.objects.filter(link=reply)
    context = {'comment':comment, 'reply':reply,
               'rep_attachments':rep_attch, 'error':error, 'username':user}
    return render(request, 'tracking/reply_detail.html', context)


@login_required
def comment_reply_add(request, com_id):    
    user = request.user 
    error = None
    if request.method == 'POST':
        add_form = ReplyAddForm(False, request.POST )
        if add_form.is_valid():
            post_info = add_form.cleaned_data
            resp, error  = _add_new_reply(request, post_info, user, com_id)
            if not error:
                return resp
    else:
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

        rev = comment.revision.first()
        _update_subscriptions(drawing=rev.drawing, mod_date=new_rep['mod_date'],
                              mod_by=new_rep['mod_by'],
                              mod_info='add reply({}) on {}'.format(reply.number,
                                                                    comment))

        resp = httprespred(reverse('tracking:reply_detail',
                                   args=[comment.id, new_rep['number']]))
    return resp, error


@login_required
def reply_edit(request, com_id, rep_no):
    user = request.user

    error = None
    reply = None
    comment = None
    if request.method == 'POST':
        edit_form = ReplyAddForm(True, request.POST)
        if edit_form.is_valid():
            post_info = edit_form.cleaned_data
            reply, comment, error = _update_reply_info(com_id, rep_no,
                                               post_info, user)
    else:
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

        rev = comment.revision.first()
        _update_subscriptions(drawing=rev.drawing, mod_date=info['mod_date'],
                              mod_by=info['mod_by'],
                              mod_info='edit reply({}) on {}'.format(reply.first().number,
                                                                     comment))

    return reply.first(), comment, error

