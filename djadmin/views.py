# -*- coding: utf-8 -*-

import base64
import os
import json
import urllib2
import uuid
import datetime
import requests
import sys
import time

reload(sys)  
sys.setdefaultencoding('utf8')

from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.db import connection
from django.http import HttpResponse, Http404

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from django.template.defaulttags import register
from django.utils.http import (base36_to_int, is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode)
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from djadmin.models import SiteInfo, MenuInfo
from tasks.models import *

from usercenter.forms import UserCreationForm
from usercenter.models import User

class DjadminCenter(View):

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'login':
            return self.login(request)
        elif slug == 'logout':
            return self.logout(request)
        raise PermissionDenied

    def login(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        context = {"status": 0}
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_staff:
            auth.login(request, user)
        elif user is not None:
            context["status"] = -1
            context["errors"] = []
            context["errors"].append('用户名权限不够！')
        else:
            context["status"] = -1
            context["errors"] = []
            context["errors"].append(u'用户名或密码错误！')
        return HttpResponse(json.dumps(context), content_type="application/json")

    def logout(self, request):
        auth.logout(request)
        return HttpResponse({"status": 0})

def login(request):
    site_info = SiteInfo.objects.first()
    context = {'site_info': site_info}
    return render(request, 'djadmin/login.html', context)

@staff_member_required(login_url='/djadmin/login')
def main(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')

    stats = {}
    stats['task_now_num'] = TaskInfo.objects.filter(task_status_id = 4).count()
    stats['task_num'] = TaskInfo.objects.count()
    stats['user_num'] = get_user_model().objects.count()
    stats['user_today_num'] = get_user_model().objects.filter(last_login__gte=date.today()).count()
    stats['facetrack_num'] = FaceTrack.objects.exclude(status = 2).count()
    stats['facetrack_total'] = FaceTrack.objects.filter(status = 2).count()
    stats['person_today_num'] = Person.objects.filter(created_time__gte=date.today(), isdeleted=0).count()
    stats['person_num'] = Person.objects.filter(isdeleted=0).count()

    context = {'site_info': site_info, 
        'menu_list': menu_list,
        'time_now': datetime.now(),
        'stats': stats}
    return render(request, 'djadmin/main.html', context)

@staff_member_required(login_url='/djadmin/login')
def setting(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/setting')

    if request.method == 'POST':
        site_info.site_name = request.POST.get('name')
        site_info.site_slogan = request.POST.get('slogan')
        site_info.site_athor = request.POST.get('author')
        site_info.site_keywords = request.POST.get('keywords')
        site_info.site_description = request.POST.get('description')
        site_info.site_copyright = request.POST.get('copyright')
        site_info.site_license = request.POST.get('license')
        site_info.site_email = request.POST.get('email')
        site_info.site_phone = request.POST.get('phone')
        site_info.save()
        messages.add_message(request, messages.INFO, u'系统设置信息保存成功！')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now}
    return render(request, 'djadmin/setting.html', context)

@staff_member_required(login_url='/djadmin/login')
def menu(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/menu')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now}
    return render(request, 'djadmin/menu.html', context)

@staff_member_required(login_url='/djadmin/login')
def addMenu(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/menu')

    if request.method == 'POST':
        name = request.POST.get('name')
        pid = request.POST.get('pid')
        link = request.POST.get('link')
        order = request.POST.get("order")
        visible = request.POST.get("visible")
        menu = MenuInfo(menu_name=name, menu_pid=pid, menu_link=link, menu_order=order, menu_visible=visible)
        menu.save()
        messages.add_message(request, messages.INFO, u'菜单信息添加成功！')
        return redirect('/djadmin/menu')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now}
    return render(request, 'djadmin/addmenu.html', context)

@staff_member_required(login_url='/djadmin/login')
def changeMenu(request, menu_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/menu')

    menu = get_object_or_404(MenuInfo, id=menu_id)
    if request.method == 'POST':
        menu.menu_name = request.POST.get('name')
        menu.menu_pid = request.POST.get('pid')
        menu.menu_link = request.POST.get('link')
        menu.menu_order = request.POST.get("order")
        menu.menu_visible = request.POST.get("visible")
        menu.save()
        messages.add_message(request, messages.INFO, u'菜单信息保存成功！')
        return redirect('/djadmin/menu')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu': menu,
            'menu_now': menu_now}
    return render(request, 'djadmin/changemenu.html', context)

@staff_member_required(login_url='/djadmin/login')
def deleteMenu(request, menu_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/menu')

    menu = get_object_or_404(MenuInfo, id=menu_id)
    menu.delete()
    messages.add_message(request, messages.INFO, u'菜单信息删除成功！')
    return redirect('/djadmin/menu')

''' user '''
@staff_member_required(login_url='/djadmin/login')
def user(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/user')

    user_list = get_user_model().objects.all()
    keyword = request.GET.get('q')
    if keyword and len(keyword):
        user_list = user_list.filter(username=keyword.encode('utf-8'))

    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, 15)
    try:
        page = int(page)
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = []

    if page >= 5:
        page_range = list(paginator.page_range)[page-5: page+4]
    else:
        page_range = list(paginator.page_range)[0: page+4]

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now,
            'page_range': page_range,
            'users': users,
            'query_num': len(user_list)}
    return render(request, 'djadmin/user.html', context)

@staff_member_required(login_url='/djadmin/login')
def addUser(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/user')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            messages.add_message(request, messages.INFO, u'添加用户成功！')
            return redirect('/djadmin/user')
        else:
            for k, v in form.errors.items():
                messages.add_message(request, messages.INFO, v.as_text())

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now}
    return render(request, 'djadmin/adduser.html', context)

@staff_member_required(login_url='/djadmin/login')
def changeUserPassword(request, user_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/user')

    user = get_object_or_404(get_user_model(), id=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.add_message(request, messages.INFO, u'用户信息编辑成功！')
            return redirect('/djadmin/user')
        else:
            for k, v in form.errors.items():
                messages.add_message(request, messages.INFO, k + ' ' + v.as_text())

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'user': user,
            'menu_now': menu_now}
    return render(request, 'djadmin/changepassword.html', context)

@staff_member_required(login_url='/djadmin/login')
def changeUserProfile(request, user_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/user')

    user = get_object_or_404(get_user_model(), id=user_id)
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.address = request.POST.get('address')
        user.phone = request.POST.get('phone')
        user.intro = request.POST.get('intro')
        if len(request.FILES):
            avatar_blob = request.FILES['upload-avatar']
            avatar_path = 'static/avatar/%s.jpg' % user_id
            with open(avatar_path, 'wb+') as destination:
                for chunk in avatar_blob.chunks():
                    destination.write(chunk)
            user.img = '/' + avatar_path
        user.save()
        messages.add_message(request, messages.INFO, u'用户信息保存成功！')
        return redirect('/djadmin/user')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'user': user,
            'menu_now': menu_now}
    return render(request, 'djadmin/changeprofile.html', context)

@staff_member_required(login_url='/djadmin/login')
def task(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/task')

    task_list = TaskInfo.objects.order_by('-created_time')
    keyword = request.GET.get('q')
    if keyword and len(keyword):
        task_list = task_list.filter(task_name__contains=keyword.encode('utf-8'))

    page = request.GET.get('page', 1)
    paginator = Paginator(task_list, 15)
    try:
        page = int(page)
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = []

    if page >= 5:
        page_range = list(paginator.page_range)[page-5: page+4]
    else:
        page_range = list(paginator.page_range)[0: page+4]

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now,
            'page_range': page_range,
            'tasks': tasks,
            'query_num': len(task_list)}
    return render(request, 'djadmin/task.html', context)

@staff_member_required(login_url='/djadmin/login')
def addTask(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/task/add')

    if request.method == 'POST':
        name = request.POST.get('name')
        keywords = request.POST.get('keywords')
        flag = request.POST.get('flag')
        description = request.POST.get('description')
        task = TaskInfo(task_name=name, 
            task_keywords=keywords,
            task_flag=flag,
            task_description=description,
            task_status=TaskStatus.objects.get(id=1))
        task.save()
        messages.add_message(request, messages.INFO, u'创建任务成功！')
        return redirect('/djadmin/task')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now}
    return render(request, 'djadmin/addtask.html', context)

@staff_member_required(login_url='/djadmin/login')
def changeTask(request, task_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/task')

    task = get_object_or_404(TaskInfo, id=task_id)
    if request.method == 'POST':
        task.task_name = request.POST.get('name')
        task.task_keywords = request.POST.get('keywords')
        task.task_flag = request.POST.get('flag')
        task.task_description = request.POST.get('description')
        task.save()
        messages.add_message(request, messages.INFO, u'任务信息保存成功！')
        return redirect('/djadmin/task')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'task': task,
            'menu_now': menu_now}
    return render(request, 'djadmin/changetask.html', context)

@staff_member_required(login_url='/djadmin/login')
def uploadTask(request, task_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/task')

    task = get_object_or_404(TaskInfo, id=task_id)
    if request.method == 'POST':
        if len(request.FILES):
            upload_blob = request.FILES['upload-data']
            data_path = 'static/task/%s.json' % task_id
            with open(data_path, 'wb+') as destination:
                for chunk in upload_blob.chunks():
                    destination.write(chunk)

            task.data_path = '/' + data_path
            task.task_status = TaskStatus.objects.get(id=2)
            task.save()

            messages.add_message(request, messages.INFO, u'上传任务数据成功！')
            return redirect('/djadmin/task')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'task': task,
            'menu_now': menu_now}
    return render(request, 'djadmin/uploadtask.html', context)

@register.filter
def divide(value, arg):
    try:
        value = int(value)
        arg = float(arg)
        if arg:
            return value/arg
    except:
        pass
    return None

@staff_member_required(login_url='/djadmin/login')
def showDetail(request, task_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/task')

    task_progress = {}
    task_progress['total'] = FaceTrack.objects.filter(task_id=task_id).count()
    task_progress['valid'] = FaceTrack.objects.filter(task_id=task_id, status=2, isdeleted=0).count()
    task_progress['skipped'] = FaceTrack.objects.filter(task_id=task_id, status=2, isdeleted=1).count()
    task_progress['progress'] = (task_progress['valid'] + task_progress['skipped']) / float(task_progress['total']) * 100

    task = get_object_or_404(TaskInfo, id=task_id)
    task_statistics = TaskStatistics.objects.filter(task_id=task_id).order_by('proc_date')
    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'task': task,
            'task_progress': task_progress,
            'stats': task_statistics,
            'menu_now': menu_now}
    return render(request, 'djadmin/showdetail.html', context)

@staff_member_required(login_url='/djadmin/login')
def viewTask(request, task_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/task')

    q = request.GET.get('q')
    if q and len(q) == 36:
        query = "SELECT facetrack.id, facetrack_id, image_path, tracking_time, person_id, finished_time, username " \
            "FROM LavaFace.facetrack " \
            "left join usercenter_user on user_id = usercenter_user.id " \
            "WHERE task_id = %s and status = 2 and isdeleted = 0 and facetrack_id = '%s' ORDER BY finished_time DESC" % (task_id, q)
    elif q:
        user = get_object_or_404(get_user_model(), username=q)
        query = "SELECT facetrack.id, facetrack_id, image_path, tracking_time, person_id, finished_time, username " \
            "FROM LavaFace.facetrack " \
            "left join usercenter_user on user_id = usercenter_user.id " \
            "WHERE task_id = %s and status = 2 and isdeleted = 0 and user_id = %s ORDER BY finished_time DESC" % (task_id, user.id)
    else:
        q = ''
        query = 'SELECT facetrack.id, facetrack_id, image_path, tracking_time, person_id, finished_time, username ' \
            'FROM LavaFace.facetrack ' \
            'left join usercenter_user on user_id = usercenter_user.id ' \
            'WHERE task_id = ' + task_id + ' and status = 2 and isdeleted = 0 ORDER BY finished_time DESC'

    facetrack_list = []
    with connection.cursor() as cursor:
        cursor.execute(query)
        for record in cursor.fetchall():
            facetrack_list.append({
                'id': record[0],
                'facetrack_id': record[1],
                'image_path': record[2],
                'tracking_time': record[3],
                'person_id': record[4],
                'finished_time': record[5],
                'finished_by': record[6]
            })

    page = request.GET.get('page', 1)
    paginator = Paginator(facetrack_list, 15)
    try:
        page = int(page)
        facetracks = paginator.page(page)
    except PageNotAnInteger:
        facetracks = paginator.page(1)
    except EmptyPage:
        facetracks = []

    if page >= 5:
        page_range = list(paginator.page_range)[page-5: page+4]
    else:
        page_range = list(paginator.page_range)[0: page+4]

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now,
            'page_range': page_range,
            'facetracks': facetracks,
            'task_id': task_id,
            'query': q,
            'query_num': len(facetrack_list)}
    return render(request, 'djadmin/viewtask.html', context)

@staff_member_required(login_url='/djadmin/login')
def person(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/person')

    person_list = Person.objects.filter(isdeleted=0).order_by('-facetracks_num')
    keyword = request.GET.get('q')
    if keyword and len(keyword):
        person_list = person_list.filter(name__contains=keyword.encode('utf-8'))

    page = request.GET.get('page', 1)
    paginator = Paginator(person_list, 15)
    try:
        page = int(page)
        persons = paginator.page(page)
    except PageNotAnInteger:
        persons = paginator.page(1)
    except EmptyPage:
        persons = []

    if page >= 5:
        page_range = list(paginator.page_range)[page-5: page+4]
    else:
        page_range = list(paginator.page_range)[0: page+4]

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now,
            'page_range': page_range,
            'persons': persons,
            'query_num': len(person_list)}
    return render(request, 'djadmin/person.html', context)

@staff_member_required(login_url='/djadmin/login')
def addPerson(request):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/person')

    if request.method == 'POST':
        pid = str(uuid.uuid1())
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        remark = request.POST.get('remark')
        person = Person(pid=pid, name=name, gender=gender, age=age, remark=remark)
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "createperson_id",
            "params": {
                "appkey": settings.DEEP_FACE_APP_KEY,
                "id": pid,
                "info": {"sex": int(gender)}
            }
        }
        response = requests.post(settings.DEEP_FACE_URL, data=json.dumps(payload), headers=settings.DEEP_FACE_HEADERS).json()
        if response['result']['code'] <> 0:
            messages.add_message(request, messages.INFO, u'创建人物失败，请联系系统管理员！')
        else:
            person.save()
            messages.add_message(request, messages.INFO, u'创建人物成功！')
        return redirect('/djadmin/person')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now}
    return render(request, 'djadmin/addperson.html', context)

@staff_member_required(login_url='/djadmin/login')
def changePerson(request, person_id):
    site_info = SiteInfo.objects.first()
    menu_list = MenuInfo.objects.order_by('menu_order')
    menu_now = get_object_or_404(MenuInfo, menu_link='/djadmin/person')

    person = get_object_or_404(Person, id=person_id)
    if request.method == 'POST':
        person.name = request.POST.get('name')
        person.gender = request.POST.get('gender')
        person.age = request.POST.get('age')
        person.remark = request.POST.get('remark')
        person.save()
        messages.add_message(request, messages.INFO, u'人物信息保存成功！')
        return redirect('/djadmin/person')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'person': person,
            'menu_now': menu_now}
    return render(request, 'djadmin/changeperson.html', context)

@staff_member_required(login_url='/djadmin/login')
def viewPersonFacetrack(request, person_id):
    if len(person_id) >= 16:
        person = get_object_or_404(Person, pid=person_id)
    else:
        person = get_object_or_404(Person, id=person_id)

    facetrack_list = FaceTrack.objects.filter(person_id=person.pid, isdeleted=0).order_by('-finished_time')
    paginator = Paginator(facetrack_list, 10)
    page = request.GET.get('page', 1)
    try:
        page = int(page)
        facetrack_matched = paginator.page(page)
        facetrack_new_object_list = []
        for facetrack_object in facetrack_matched.object_list:
            facetrack_id = facetrack_object.facetrack_id
            facetrack_image_path = facetrack_object.image_path
            facetrack_src_id = facetrack_object.src_id
            facetrack_tracking_time = facetrack_object.tracking_time
            facetrack_imgs = facetrack_object.facetrackimage_set.filter(isdeleted=0)
            facetrack_finished_by = get_object_or_404(get_user_model(), id=facetrack_object.user_id).username
            if facetrack_tracking_time is None:
                facetrack_tracking_time = '1970-01-01 00:00:00'
            else:
                facetrack_tracking_time = facetrack_object.tracking_time.strftime("%Y-%m-%d %H:%M:%S")
            facetrack_new_object_list.append({
                'facetrack_id': facetrack_id,
                'big_image': facetrack_image_path,
                'src_id': facetrack_src_id,
                'finished_by': facetrack_finished_by,
                'tracking_time': facetrack_tracking_time,
                'facetrack_imgs': facetrack_imgs,
                'facetrack_createdate': facetrack_tracking_time
            })
        facetrack_matched.object_list = facetrack_new_object_list
    except PageNotAnInteger:
        facetrack_matched = paginator.page(1)
    except EmptyPage:
        facetrack_matched = []

    if page >= 5:
        page_range = list(paginator.page_range)[page-5: page+4]
    else:
        page_range = list(paginator.page_range)[0: page+4]

    context = {'page_range': page_range,
            'person': person,
            'facetracks': facetrack_matched,
            'query_num': len(facetrack_list)}
    return render(request, 'djadmin/viewpersonfacetrack.html', context)

@staff_member_required(login_url='/djadmin/login')
def deletePersonFacetrack(request, person_id):
    http_referer_url = request.META.get('HTTP_REFERER')
    facetrack_id = request.GET.get('facetrack_id')
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "cancelfacetrackfromperson",
        "params": {
            "appkey": settings.DEEP_FACE_APP_KEY,
            "id_facetrack": facetrack_id
        }
    }
    response = requests.post(settings.DEEP_FACE_URL, data=json.dumps(payload), headers=settings.DEEP_FACE_HEADERS).json()
    if response['result']['code'] <> 0:
        print(response)
        messages.add_message(request, messages.INFO, u'删除FaceTrack序列失败，请联系系统管理员！')
        return redirect(http_referer_url)
    else:
        facetrack = FaceTrack.objects.get(facetrack_id=facetrack_id)
        facetrack.isdeleted = 1
        facetrack.save()
        messages.add_message(request, messages.INFO, u'删除FaceTrack序列成功！')
        return redirect(http_referer_url)

@staff_member_required(login_url='/djadmin/login')
def matchPerson2Person(request, person_id):
    if len(person_id) >= 16:
        person = get_object_or_404(Person, pid=person_id)
    else:
        person = get_object_or_404(Person, id=person_id)

    person_matched = []
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "matchperson2person",
        "params": {
            "appkey": settings.DEEP_FACE_APP_KEY,
   	    "id": person.pid,
            "src_ids": []
        }
    }
    response = requests.post(settings.DEEP_FACE_URL, data=json.dumps(payload), headers=settings.DEEP_FACE_HEADERS).json()
    if response['result']['code'] <> 0:
        messages.add_message(request, messages.INFO, u'Person检索失败，请联系系统管理员！')
    else:
        if response['result']['results'] <> None:
            transaction_id = response['result']['results']['transId']

            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "getmatchperson2personresult",
                "params": {
                    "appkey": settings.DEEP_FACE_APP_KEY,
                    "id_person": person.pid,
   	            "id_trans": transaction_id
                }
            }

            response = requests.post(settings.DEEP_FACE_URL, data=json.dumps(payload), headers=settings.DEEP_FACE_HEADERS).json()
            if response['result']['results'] <> None and response['result']['results']['count']:
                for person_id in response['result']['results']['matches']:
                    payload = {
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "getpersoninfo",
                        "params": {
                            "appkey": settings.DEEP_FACE_APP_KEY,
   	                    "id": person_id
                        }
                    }

                    response = requests.post(settings.DEEP_FACE_URL, data=json.dumps(payload), headers=settings.DEEP_FACE_HEADERS).json()
                    if response['result']['code'] == 0:
                        person_images = []
                        for img in response['result']['results']['imgs']:
                            url = '/image/?type=1&id=' + person_id + '&fn=' + img
                            person_images.append(url)

                        person_matched.append({
                            'person_id': person_id,
                            'person_images': person_images
                        })

    context = {'page_range': page_range,
            'persons': person_matched,
            'query_num': len(person_list)}
    return render(request, 'djadmin/showsimilarperson.html', context)

@staff_member_required(login_url='/djadmin/login')
def statistics(request):
    apiid = request.GET.get("apiid")
    query = 'select date(finished_time) as finished_date, count(*) FROM facetrack where ' \
        + 'to_days(now()) - to_days(finished_time) <= 20 group by finished_date'
    
    context = {'status': 0}
    context['data'] = {}
    context['data']['stats'] = []

    items = {}
    with connection.cursor() as cursor:
        cursor.execute(query)
        for record in cursor.fetchall():
            items[str(record[0])] = record[1]

    now = datetime.now()
    for n in range(0, 20):
        record = {}
        record['date'] = (now - timedelta(days=n)).strftime('%Y-%m-%d')
        record['count'] = items.get(record['date'], 0)
        context['data']['stats'].append(record)
    return HttpResponse(json.dumps(context), content_type="application/json")

