# -*- coding: utf-8 -*-
from django.conf.urls import url
from usercenter.views import UserCenter

from . import views

urlpatterns = [
        url(r'^$', views.login, name="login"),
        url(r'^login$', views.login, name="login"),
        # 用户登录首页
        url(r'^main$', views.main, name="main"),
        # 侧边栏个人中心里，'我的资料'和'修改密码'选项
        url(r'^profile$', views.profile, name="profile"),
        url(r'^password$', views.password, name="password"),

        url(r'^person/(?P<person_id>[a-z0-9-]+)/change$', views.changePerson, name='changePerson'),
        url(r'^person/(?P<person_id>[a-z0-9-]+)/facetrack$', views.viewPersonFacetrack, name='viewPersonFacetrack'),
        url(r'^person/(?P<person_id>[a-z0-9-]+)/facetrack/delete$', views.deletePersonFacetrack, name='deletePersonFacetrack'),
        # 侧边栏任务中心里，'我的任务'和'历史记录'选项
        url(r'^task$', views.task, name="task"),
        url(r'^task/(?P<task_id>[0-9]+)/proc$', views.processTask, name='processTask'),
        url(r'^task/(?P<task_id>[0-9]+)/allocate$', views.allocateTask, name='allocateTask'),
        url(r'^task/(?P<task_id>[0-9]+)/matchfacetrack2person$', views.matchFacetrack2Person, name='matchFacetrack2Person'),
        url(r'^task/(?P<task_id>[0-9]+)/matchperson2facetrack$', views.matchPerson2Facetrack, name='matchPerson2Facetrack'),
        url(r'^task/(?P<task_id>[0-9]+)/addfacetrack2person$', views.addFacetrack2Person, name='addFacetrack2Person'),
        url(r'^task/(?P<task_id>[0-9]+)/addfacetrack2newperson$', views.addFacetrack2NewPerson, name='addFacetrack2NewPerson'),
        url(r'^task/(?P<task_id>[0-9]+)/deletefacetrackimg$', views.deleteFacetrackImg, name='deleteFacetrackImg'),
        url(r'^task/(?P<task_id>[0-9]+)/deletefacetrack$', views.deleteFacetrack, name='deleteFacetrack'),
        url(r'^task/(?P<task_id>[0-9]+)/addfacetracks2person$', views.addFacetracks2Person, name='addFacetracks2Person'),
        url(r'^log$', views.log, name="log"),
        url(r'^statistics$', views.statistics, name="statistics"),
        # 侧边栏任务中心里，'我的任务'和'历史记录'选项
        url(r'^question$', views.question, name="question"),
        url(r'^question/add$', views.addQuestion, name="addQuestion"),
        url(r'^question/(?P<question_id>[0-9]+)/$', views.showQuestion, name='showQuestion'),
        url(r'^question/(?P<question_id>[0-9]+)/comment/add$', views.addComment, name='addComment'),
        url(r'^(?P<slug>\w+)check$', UserCenter.as_view()),
        ]

