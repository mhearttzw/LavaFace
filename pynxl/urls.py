from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'pynxl.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^', include('usercenter.urls')),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^usercenter/', include('usercenter.urls')),
    url(r'^djadmin/', include('djadmin.urls')),
    url(r'^image/', include('image.urls')),
]

