"""drc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
import os
from django.conf.urls import url
from django.conf.urls import patterns
from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect as httprespred

from tracking import urls as tracking_urls
from tracking import views as tracking_views

urlpatterns = [
    url(r'^drc/admin/', admin.site.urls, name='admin'),
    url(r'^drc/favicon\.ico$', lambda x: httprespred(os.path.join(settings.STATIC_URL, 
                                                              'images', 'favicon.ico'))),
    url(r'^drc/accounts/login',auth_views.login, {'template_name': 'tracking/login.html'}, name='login'),
    url(r'^drc/accounts/logout', tracking_views.logout_view, name='logout'),
    url(r'^drc/', include(tracking_urls)),
    url(r'^', include(tracking_urls)),
    url(r'^drc/tracking/', include(tracking_urls)),
    url(r'drc/session_security/', include('session_security.urls')),
    
] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

