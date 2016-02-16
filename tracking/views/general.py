from django.contrib.auth import logout
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect as httprespred

from tracking.models import Comment

from .subscriptions import _update_subscriptions

# from tracking.tasks import test


def logout_view(request):
    ''' Logout confirmation '''
    user = request.user
    logout(request)
    return render(request, 'tracking/logout.html', {'username':user})


#---------------------- Index ------------------------
@login_required
def index(request):
    ''' Homepage '''
    user = request.user
    # t = test.delay('words')
    # print(t.get())
    return render(request, 'tracking/index.html', {'username':user})


#---------------------- Quicklinks ------------------------
@login_required
def open_comment_search(request):
    user = request.user
    coms = Comment.objects.prefetch_related('revision')\
                         .filter(status=True).order_by('-mod_date')
    context = {'comments':coms, 'username':user}
    return render(request, 'tracking/open_comments.html', context)


@login_required
def toggle_comment(request, com_id):
    user = request.user
    comment = Comment.objects.get(pk=com_id)
    if comment.owner == user or comment.owner == None:
        comment.status = not comment.status
        comment.save()
        com_stat = 'open' if comment.status else 'closed'
        _update_subscriptions(drawing=comment.revision.first().drawing, mod_date=timezone.now(),
                              mod_by=user,
                              mod_info='changed comment({}) status to {}'.format(comment.id, com_stat))

    return httprespred(reverse('tracking:comment_detail', args=[com_id]))
