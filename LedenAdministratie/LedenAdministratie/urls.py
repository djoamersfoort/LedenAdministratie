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
from django.urls import path, re_path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views, api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    re_path(r'^tinymce/', include('tinymce.urls')),
    path('members/<filter_slug>/', views.MemberListView.as_view(), name='members'),
    path('members/', views.MemberListView.as_view(), name='members'),
    path('export/', views.ExportView.as_view(), name='export'),
    path('member/edit/<int:pk>/', views.MemberUpdateView.as_view(), name='lid_edit'),
    path('member/delete/<int:pk>/', views.MemberDeleteView.as_view(), name='lid_delete'),
    path('member/create/', views.MemberCreateView.as_view(), name='lid_create'),
    path('member/addnote/<int:member_id>/', views.MemberAddNoteView.as_view(), name='lid_addnote'),
    path('member/delnote/<int:pk>', views.MemberDeleteNoteView.as_view(), name='lid_delnote'),
    path('member/editnote/<int:pk>', views.MemberEditNoteView.as_view(), name='lid_editnote'),
    path('todolist/', views.TodoListView.as_view(), name='todolist'),
    path('invoice/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoice/create/<int:member_id>/', views.InvoiceCreateView.as_view(), name='invoice_create_for'),
    path('invoice/display/<int:pk>', views.InvoiceDisplayView.as_view(), name='invoice_display'),
    path('invoice/delete/<int:pk>', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoice/payment/', views.InvoicePaymentView.as_view(), name='invoice_payment'),
    path('invoice/pay_full/<int:pk>', views.InvoicePayFullView.as_view(), name='invoice_pay_full'),
    path('invoice/pay_part/<int:pk>', views.InvoicePayPartView.as_view(), name='invoice_pay_part'),
    path('invoice/pay_part/<int:pk>/<int:member_id>', views.InvoicePayPartView.as_view(), name='invoice_pay_part'),
    path('invoice/send/', views.InvoiceSendView.as_view(), name='invoice_send'),
    path('email/send/', views.EmailSendView.as_view(), name='email_send'),
    path('email/log/', views.EmailLogView.as_view(), name='email_log'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('api/v1/smoelenboek/', api.ApiV1Smoelenboek.as_view()),
    path('api/v1/smoelenboek/<int:pk>/', api.ApiV1SmoelenboekUser.as_view()),
    path('api/v1/smoelenboek/<str:day>/', api.ApiV1Smoelenboek.as_view()),
    path('api/v1/idp/details/<str:fields>', api.ApiV1IDPGetDetails.as_view()),
    path('api/v1/idp/verify/<str:fields>', api.ApiV1IDPVerify.as_view()),
    path('api/v1/idp/avatar', api.ApiV1IDPAvatar.as_view()),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('logged_in/', views.LoggedInView.as_view(), name='logged_in'),
    path('', auth_views.LoginView.as_view(), name='login'),
]
