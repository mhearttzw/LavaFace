# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser

from djadmin.models import SiteInfo, MenuInfo


class string_with_title(str):
    def __new__(cls, value, title):
        instance = str.__new__(cls, value)
        instance._title = title
        return instance

    def title(self):
        return self._title

    __copy__ = lambda self: self
    __deepcopy__ = lambda self, memodict: self


# 自定义用户模型
class User(AbstractUser):
    last_login_ip = models.CharField(max_length=30, blank=True, null=True, verbose_name='登陆IP')
    img = models.CharField(max_length=200, default='/static/avatar/default.gif', verbose_name='头像地址')
    intro = models.CharField(max_length=200, blank=True, null=True, verbose_name='简介')
    address = models.CharField(max_length=200, verbose_name='联系地址', blank=True, null=True)
    phone = models.CharField(max_length=200, verbose_name='联系电话', blank=True, null=True)

    class Meta(AbstractUser.Meta):
        # 如果一个模型位于标准的位置之外（应用的models.py 或models 包），该模型必须定义它属于哪个应用
        app_label = string_with_title('usercenter', u"用户管理")


class Menu(models.Model):
    name = models.CharField(u'菜单名称', max_length=30)
    pid = models.IntegerField(u'上级菜单', null=True)
    link = models.CharField(u'链接', max_length=255, null=True)
    order = models.IntegerField(u'排序', null=True)
    visible = models.IntegerField(u'是否可见', default=1, null=True)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True, null=True)

    class Meta:
        # 对象的一个易于理解的名称，为单数；如果此项没有设置，Django会把类名拆分开来作为自述名，比如CamelCase 会变成camel case
        verbose_name = u'用户中心管理'
        # 该对象复数形式的名称，如果此项没有设置，Django 会使用 verbose_name + "s"。
        verbose_name_plural = u'用户中心菜单管理'

