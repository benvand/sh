from django.conf.urls import patterns, include, url
import views
import config

urlpatterns = patterns('',)

if config.webpage:
    urlpatterns += patterns('', url( 'distance/$', views.Distance.as_view(), ))#name='distance' ))

if config.api:
    api_prefix = "distance/api/"
    urlpatterns += patterns('', url( '%s$' % api_prefix, views.Api.as_view(), ))# name='distance' ))
    urlpatterns += patterns('', url( '%sip$' % api_prefix, views.ApiIP.as_view(), ))# name='distance' ))
    urlpatterns += patterns('', url( '%spc$' % api_prefix, views.ApiPostcode.as_view(), ))# name='distance' ))
    urlpatterns += patterns('', url( '%sll$' % api_prefix, views.ApiLatLong.as_view(), ))# name='distance' ))