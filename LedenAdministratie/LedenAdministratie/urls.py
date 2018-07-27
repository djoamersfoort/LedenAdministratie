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
from django.urls import path, include
from django.contrib import admin
from LedenAdministratie import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('ledenlijst/<speltak>/', views.ledenlijst, name='ledenlijst'),
    path('ledenlijst/', views.ledenlijst, name='ledenlijst'),
    path('logoff/', views.logoff, name='logoff'),
    path('export/', views.export, name='export'),
    path('do_export/<speltak>/', views.do_export, name='do_export'),
    path('lid_edit/<int:pk>/', views.LidUpdateView.as_view(), name='lid_edit'),
    path('lid_delete/<int:pk>/', views.LidDeleteView.as_view(), name='lid_delete'),
    path('lid_create/', views.LidCreateView.as_view(), name='lid_create'),
    path('aanmelden/', views.LidAanmeldView.as_view(), name='lid_aanmelden'),
    path('aanmelden_ok/', views.aanmelden_ok, name='aanmelden_ok'),
    path('/', views.login, name='login'),
]
