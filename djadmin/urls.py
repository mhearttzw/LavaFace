from django.conf.urls import url
from djadmin.views import DjadminCenter

from . import views

urlpatterns = [
        url(r'^$', views.login, name="login"),
        url(r'^login$', views.login, name="login"),
        url(r'^main$', views.main, name="main"),
        url(r'^setting$', views.setting, name="setting"),
        url(r'^menu$', views.menu, name="menu"),
        url(r'^menu/add$', views.addMenu, name="addMenu"),
        url(r'^menu/(?P<menu_id>[0-9]+)/change$', views.changeMenu, name='changeMenu'),
        url(r'^menu/(?P<menu_id>[0-9]+)/delete$', views.deleteMenu, name='deleteMenu'),
        url(r'^person$', views.person, name="person"),
        url(r'^person/add$', views.addPerson, name="addPerson"),
        url(r'^person/(?P<person_id>[0-9]+)/change$', views.changePerson, name='changePerson'),
        url(r'^person/(?P<person_id>[0-9]+)/delete$', views.deletePerson, name='deletePerson'),
        url(r'^person/(?P<person_id>[a-z0-9-]+)/viewpersonfacetrack$', views.viewPersonFacetrack, name='viewPersonFacetrack'),
        url(r'^person/(?P<person_id>[a-z0-9-]+)/facetrack/delete$', views.deletePersonFacetrack, name='deletePersonFacetrack'),
        url(r'^person/(?P<person_id>[0-9]+)/image/add$', views.addImage, name='addImage'),
        url(r'^person/(?P<person_id>[0-9]+)/image/delete$', views.deleteImage, name='deleteImage'),
        url(r'^task$', views.task, name="task"),
        url(r'^task/add$', views.addTask, name="addTask"),
        url(r'^task/(?P<task_id>[0-9]+)/change$', views.changeTask, name='changeTask'),
        url(r'^task/(?P<task_id>[0-9]+)/upload$', views.uploadTask, name='uploadTask'),
        url(r'^task/(?P<task_id>[0-9]+)/detail$', views.showDetail, name='showDetail'),
        url(r'^task/(?P<task_id>[0-9]+)/view$', views.viewTask, name='viewTask'),
        url(r'^user$', views.user, name="user"),
        url(r'^user/add$', views.addUser, name="addUser"),
        url(r'^user/(?P<user_id>[0-9]+)/changepassword$', views.changeUserPassword, name='changeUserPassword'),
        url(r'^user/(?P<user_id>[0-9]+)/changeprofile$', views.changeUserProfile, name='changeUserProfile'),
        url(r'^(?P<slug>\w+)check$', DjadminCenter.as_view()),
        url(r'^statistics$', views.statistics, name="statistics"),
        ]

