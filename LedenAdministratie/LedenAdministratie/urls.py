"""LedenAdministratie URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from LedenAdministratie import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('allauth.socialaccount.providers.openid.urls')),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^ledenlijst/(.*)/$', views.ledenlijst, name='ledenlijst'),
    url(r'^ledenlijst/$', views.ledenlijst, name='ledenlijst'),
    url(r'^logoff/$', views.logoff, name='logoff'),
    url(r'^export/$', views.export, name='export'),
    url(r'^do_export/(.*)/$', views.do_export, name='do_export'),
    url(r'^lid_edit/(?P<pk>[0-9]+)/$', views.LidUpdateView.as_view(), name='lid_edit'),
    url(r'^lid_delete/(?P<pk>[0-9]+)/$', views.LidDeleteView.as_view(), name='lid_delete'),
    url(r'^lid_create/$', views.LidCreateView.as_view(), name='lid_create'),
    url(r'^aanmelden/$', views.LidAanmeldView.as_view(), name='lid_aanmelden'),
    url(r'^aanmelden_ok/$', views.aanmelden_ok, name='aanmelden_ok'),
    url(r'^$', views.login, name='login'),
]
