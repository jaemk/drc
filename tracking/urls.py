from django.conf.urls import url

from . import views

app_name = 'tracking'
urlpatterns = [
    # Home
    url(r'^$', views.index, name='index'),

    # Search (drawing, revision)
    url(r'^search/drawing/$', views.drawing_search, name='drawing_search'),
    url(r'^search/revision/$', views.revision_search, name='revision_search'),

    # quicklinks
    url(r'^search/open_comments/$', views.open_comment_search, name='open_comments'),
    url(r'^comment/toggle/(?P<com_id>[0-9_]+)/$', views.toggle_comment, name='toggle_comment'),

    # Drawing (detail, edit, add)
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/$',
        views.drawing_detail, name='drawing_detail'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/edit/$',
        views.drawing_edit, name='drawing_edit'),
    url(r'^add/drawing/$', views.drawing_add, name='drawing_add'),

    # Revision (detail, add from drawing, add, edit)
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/rev/(?P<rev_no>[a-zA-Z0-9_\.-]+)/$',
        views.revision_detail, name='revision_detail'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/add/rev/$',
        views.drawing_revision_add, name='drawing_revision_add'),
    url(r'^add/revision/$', views.revision_add, name='revision_add'),
    url(r'^drawing/(?P<drawing_name>[a-zA-Z0-9_-]+)/edit/rev/(?P<rev_no>[a-z-A-Z0-9_\.-]+)/$',
        views.revision_edit, name='revision_edit'),

    # Comment (detail, add)
    url(r'^comment/(?P<com_id>[0-9_]+)/$',
        views.comment_detail, name='comment_detail'),
    url(r'^add/comment/on/(?P<drawing_name>[a-zA-Z0-9_-]+)/$',
        views.drawing_comment_add, name='drawing_comment_add'),
    url(r'^add/comment/$', views.comment_add, name='comment_add'),
    url(r'^comment/(?P<com_id>[0-9_]+)/edit/$', views.comment_edit, name='comment_edit'),

    # Reply (detail)
    url(r'^comment/(?P<com_id>[0-9_]+)/reply/(?P<rep_id>[0-9_]+)/$',
        views.reply_detail, name='reply_detail'),

    # Attachment (add, serve, remove)
    url(r'^attachment/add/(?P<item_type>(drawing|revision|comment|reply))/(?P<item_id>[0-9_]+)/$',
        views.add_attachment, name='add_attachment'),
    url(r'^attachment/serve/(?P<file_type>(drawing|revision|comment|reply))/(?P<file_id>[0-9_]+)/$',
        views.serve_attachment, name='serve_attachment'),
    url(r'^attachment/remove/(?P<item_type>(drawing|revision|comment|reply))/(?P<item_id>[0-9_]+)/$',
        views.remove_attachment, name='remove_attachment'),

    
    ]

