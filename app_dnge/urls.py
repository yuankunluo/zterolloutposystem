__author__ = 'yuluo'

from django.conf.urls import patterns, url

import views as views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^update/$', views.update, name='update'),
)