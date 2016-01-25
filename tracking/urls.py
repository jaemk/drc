from django.conf.urls import url

from . import views

app_name = 'tracking'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^search/drawing/$', views.drawing_search, name='drawing_search'),
    url(r'^search/revision/$', views.revision_search, name='revision_search'),
    # url(r'^search/results/$', views.search_do, name='search_do'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/$',
        views.drawing_detail, name='drawing_detail'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/attachment/(?P<file_id>[a-zA-Z0-9_]+)/$',
        views.serve_attachment, name='serve_attachment'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/edit/$',
        views.drawing_edit, name='drawing_edit'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/rev/(?P<rev_no>[a-zA-Z0-9_\.-]+)/$',
        views.revision_detail, name='revision_detail'),
    url(r'^comment/(?P<com_id>[0-9_]+)/$',
        views.comment_detail, name='comment_detail'),
    url(r'^attachment/add/(?P<type>[a-z]+)/(?P<item_id>[0-9_]+)/$',
        views.add_attachment, name='add_attachment'),

    # quicklinks
    url(r'^search/open_comments/$', views.open_comment_search, name='open_comments'),
    ]

