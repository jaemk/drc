from django.shortcuts import render
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from tracking.models import Drawing
from tracking.models import DrawingSubscription


#---------------------------  Subscriptions -----------------------------
@login_required
def subscribe_drawing(request, drawing_name, go_to):
    ''' toggle drawing subscriptions '''
    user = request.user
    drawing = Drawing.objects.get(name=drawing_name)
    sub = DrawingSubscription.objects.filter(drawing=drawing, user=user)
    if not sub.exists():
        newsub = DrawingSubscription(drawing=drawing, user=user)
        newsub.save()
    elif sub.count() == 1:
        sub.first().delete()

    if go_to == 'drawing':
        return httprespred(reverse('tracking:drawing_detail', args=[drawing_name]))
    elif go_to == 'list':
        return httprespred(reverse('tracking:subscriptions'))


@login_required
def subscribed_drawings(request):
    user = request.user
    subs = DrawingSubscription.objects.filter(user=user).order_by('-last_mod_date')
    context = {'username':user, 'subs':subs}
    return render(request, 'tracking/subscribed_drawings.html', context)


def _update_subscriptions(drawing=None, drawing_name=None,
                          mod_date=None, mod_by=None, mod_info=None):
    if drawing:
        subs = DrawingSubscription.objects.filter(drawing=drawing)
    else:
        subs = DrawingSubscription.objects.filter(drawing__name=drawing_name)
    info = {'last_mod_date':mod_date, 'last_mod_by':mod_by, 'mod_info':mod_info}
    subs.update(**info)