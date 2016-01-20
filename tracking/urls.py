from django.conf.urls import url

from . import views

app_name = 'tracking'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^search/drawing/$', views.drawing_search, name='drawing_search'),
    # url(r'^search/results/$', views.search_do, name='search_do'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_]+)/$',
        views.drawing_detail, name='drawing_detail'),
    url(r'^attachment/(?P<file_name>[a-zA-Z0-9_]+)/$',
        views.attachment, name='attachment'),

    ]

