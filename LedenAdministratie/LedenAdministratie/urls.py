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
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('members/<filter_slug>/', views.MemberListView.as_view(), name='members'),
    path('members/', views.MemberListView.as_view(), name='members'),
    path('logoff/', views.logoff, name='logoff'),
    path('export/', views.export, name='export'),
    path('do_export/<filter_slug>/', views.do_export, name='do_export'),
    path('member/edit/<int:pk>/', views.LidUpdateView.as_view(), name='lid_edit'),
    path('member/delete/<int:pk>/', views.LidDeleteView.as_view(), name='lid_delete'),
    path('member/create/', views.LidCreateView.as_view(), name='lid_create'),
    path('member/addnote/<int:member_id>/', views.LidAddNoteView.as_view(), name='lid_addnote'),
    path('member/delnote/<int:pk>', views.LidDeleteNoteView.as_view(), name='lid_delnote'),
    path('member/editnote/<int:pk>', views.LidEditNoteView.as_view(), name='lid_editnote'),
    path('todolist/', views.TodoListView.as_view(), name='todolist'),
    path('invoice/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoice/create/<int:member_id>/', views.InvoiceCreateView.as_view(), name='invoice_create_for'),
    path('invoice/display/<int:pk>', views.InvoiceDisplayView.as_view(), name='invoice_display'),
    path('invoice/delete/<int:pk>', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('', views.login, name='login'),
]
