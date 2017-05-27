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

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.db import connection
from django.http import HttpResponse, Http404

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from django.template.defaulttags import register
from django.utils import timezone
from django.utils.http import (base36_to_int, is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode)
from django.utils.timesince import timesince
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from djadmin.models import SiteInfo
from tasks.models import *

from usercenter.models import Menu, User

class UserCenter(View):

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
        if user is not None:
            auth.login(request, user)
            if request.META.has_key('HTTP_X_FORWARDED_FOR'):
                user.last_login_ip = request.META['HTTP_X_FORWARDED_FOR']
            else:
                user.last_login_ip = request.META['REMOTE_ADDR']
            user.save()
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
    return render(request, 'usercenter/login.html', context)

@login_required(login_url='/usercenter/login')
def main(request):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')

    stats = {}
    stats['task_num'] = TaskInfo.objects.filter(task_status_id__gte=4).count()
    stats['user_num'] = get_user_model().objects.count()
    stats['facetrack_num'] = FaceTrack.objects.exclude(status = 2).count()
    stats['person_num'] = Person.objects.filter(isdeleted = 0).count()

    context = {'site_info': site_info, 
        'menu_list': menu_list,
        'time_now': datetime.now(),
        'stats': stats}
    return render(request, 'usercenter/main.html', context)

@login_required(login_url='/usercenter/login')
def profile(request):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/profile')

    user = get_object_or_404(get_user_model(), id=request.user.id)
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
        return redirect('/usercenter/profile')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'user': user,
            'menu_now': menu_now}
    return render(request, 'usercenter/profile.html', context)

@login_required(login_url='/usercenter/login')
def password(request):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/password')

    user = get_object_or_404(get_user_model(), id=request.user.id)
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.add_message(request, messages.INFO, u'修改密码成功！')
            return redirect('/usercenter/password')
        else:
            for k, v in form.errors.items():
                messages.add_message(request, messages.INFO, k + ' ' + v.as_text())

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'user': user,
            'menu_now': menu_now}
    return render(request, 'usercenter/password.html', context)

@login_required(login_url='/usercenter/login')
def task(request):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/task')

    task_list = TaskInfo.objects.filter(task_status_id__gte = 4, taskassign__user_id = request.user.id).order_by('-created_time')
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
    return render(request, 'usercenter/task.html', context)

@login_required(login_url='/usercenter/login')
def processTask(request, task_id):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/task')

    task = get_object_or_404(TaskInfo, id=task_id)
    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'task': task,
            'menu_now': menu_now}
    return render(request, 'usercenter/processtask.html', context)

@csrf_exempt
def allocateTask(request, task_id):
    context = {}
    context['status'] = 0
    context['message'] = 'success'

    if not TaskAssign.objects.filter(user = request.user, task_id = task_id).exists():
        context['status'] = -3
        context['message'] = u'权限不够！'
        return HttpResponse(json.dumps(context), content_type="application/json")

    facetracks_total = FaceTrack.objects.filter(task=TaskInfo.objects.get(pk=task_id)).count()
    facetracks_left = facetracks_total - FaceTrack.objects.filter(task=TaskInfo.objects.get(pk=task_id), status=2).count()
    facetracks_mine = FaceTrack.objects.filter(user_id=request.user.id, task=TaskInfo.objects.get(pk=task_id), status=2).count()
    facetracks_mine_deleted = FaceTrack.objects.filter(user_id=request.user.id, task=TaskInfo.objects.get(pk=task_id), status=2, isdeleted=1).count()

    context['data'] = {'total': facetracks_total, 'left': facetracks_left, 'mine': facetracks_mine, 'deleted': facetracks_mine_deleted, 'items': []}

    facetracks = FaceTrack.objects.filter(user_id=request.user.id, task=TaskInfo.objects.get(pk=task_id), status=1)
    if not len(facetracks):
        query = 'UPDATE facetrack SET user_id = '+ str(request.user.id) + ', status = 1, allocated_time = now() WHERE user_id is null and task_id = ' + str(task_id) + ' LIMIT 1'
        with connection.cursor() as cursor:
            affetcted_rows = cursor.execute(query)
        facetracks = FaceTrack.objects.filter(user_id=request.user.id, task=TaskInfo.objects.get(pk=task_id), status=1)

    if not len(facetracks):
        facetracks_left_num = FaceTrack.objects.filter(task=TaskInfo.objects.get(pk=task_id)).exclude(status=2).count()
        if facetracks_left_num == 0:
            task = get_object_or_404(TaskInfo, id=task_id)
            task.task_status = TaskStatus.objects.get(id=5)
            task.save()
            context['status'] = -1
            context['message'] = u'已经没有任务了！'
        else:
            context['status'] = -2
            context['message'] = u'任务紧张，请稍候刷新重试！'
    else:
        facetracks = facetracks[:1]
        for facetrack in facetracks:
            ''' 获取图片信息 '''
            images = []
            facetrack_images = facetrack.facetrackimage_set.filter(isdeleted = 0)
            for image in facetrack_images:
                url = '/image/?type=0&id=' + facetrack.facetrack_id + '&fn=' + image.img_id
                images.append(url)

            ''' 匹配结果返回 '''
            facetrack_tracking_time = facetrack.tracking_time
            if facetrack.tracking_time is None:
                facetrack_tracking_time = '1970-01-01 00:00:00'
            else:
                facetrack_tracking_time = facetrack.tracking_time.strftime("%Y-%m-%d %H:%M:%S")
            context['data']['items'].append(
                {
                    'facetrack_id': facetrack.facetrack_id,
                    'big_image': facetrack.image_path,
                    'tracking_time': facetrack_tracking_time,
                    'src_id': facetrack.src_id,
                    'remark': facetrack.remark,
                    'images': images
                }
            )
    return HttpResponse(json.dumps(context), content_type="application/json")

@csrf_exempt
def matchFacetrack2Person(request, task_id):
    context = {}
    context['status'] = 0
    context['message'] = 'success'
    context['data'] = {}

    if request.method == 'POST':
        facetrack_id = request.POST.get('facetrack_id')

        task = TaskInfo.objects.get(id = task_id)
        person_matches = None

	payload = {
	    "id": 1,
            "jsonrpc": "2.0",
	    "method": "matchfacetrack2person",
	    "params": {
                "appkey": task.task_model.model_key,
                "id": facetrack_id,
                "src_ids": []
	    }
	}
	response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
        if response['result']['code'] == 0:
            transaction_id = response['result']['results']['transId']

            while True:
                time.sleep(0.1)
	        payload = {
	            "id": 1,
                    "jsonrpc": "2.0",
	            "method": "getmatchfacetrackresult",
	            "params": {
                        "appkey": task.task_model.model_key,
                        "id_facetrack": facetrack_id,
                        "id_trans": transaction_id
	            }
	        }

	        response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
	        if response['result']['results']['count'] == -1:
                    continue
                else:
                    break

	    if response['result']['code'] == 0:
                if response['result']['results']['count'] <> 0:
                    person_matches = response['result']['results']['matchs']
                else:
                    person_matches = []
                for person_match in person_matches:
                    person_match['id'] = Person.objects.get(pid=person_match['id_person']).id
	            payload = {
	                "id": 1,
                        "jsonrpc": "2.0",
	                "method": "getpersoninfo",
	                "params": {
	                    "appkey": task.task_model.model_key,
	                    "id": person_match['id_person']
	                }
	            }
	            response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
                    if response['result']['code'] == 0:
                        person_match['images'] = []
                        for img in response['result']['results']['imgs']:
                            url = '/image/?type=1&id=' + person_match['id_person'] + '&fn=' + img
                            person_match['images'].append(url)

                        context['data'] = {
                            'facetrack_id': facetrack_id,
                            'matches': person_matches
                        }
	    else:
                context['status'] = -1
                context['message'] = u'FaceTrack匹配Person失败，请联系管理员！'
        else:
            context['status'] = -2
            context['message'] = u'FaceTrack匹配Person失败，请联系管理员！'

    return HttpResponse(json.dumps(context), content_type="application/json")

@csrf_exempt
def matchPerson2Facetrack(request, task_id):
    context = {}
    context['status'] = 0
    context['message'] = 'success'
    context['data'] = {}

    if request.method == 'POST':
        person_id = request.POST.get('person_id')

        task = TaskInfo.objects.get(id = task_id)

	payload = {
	    "id": 1,
            "jsonrpc": "2.0",
	    "method": "matchperson2facetrack",
	    "params": {
                "appkey": task.task_model.model_key,
                "id": person_id,
                "src_ids": []
	    }
	}
	response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
        transaction_id = response['result']['results']['transId']

        while True:
            time.sleep(0.1)
	    payload = {
	        "id": 1,
                "jsonrpc": "2.0",
	        "method": "getmatchpersonresult",
	        "params": {
                    "appkey": task.task_model.model_key,
                    "id_person": person_id,
                    "id_trans": transaction_id
	        }
	    }
	    response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
	    if response['result']['results']['count'] == -1:
                continue
            else:
                break

	if response['result']['code'] == 0:
            facetrack_matches = []
            for facetrack_match in response['result']['results']['matchs']:
                try:
                    facetrack = FaceTrack.objects.get(facetrack_id=facetrack_match['id_facetrack'])
                except ObjectDoesNotExist:
                    continue

                facetrack_match['big_image'] = facetrack.image_path

                facetrack_match['images'] = []
                facetrack_images = facetrack.facetrackimage_set.all()
                for image in facetrack_images:
                    url = '/image/?type=0&id=' + facetrack.facetrack_id + '&fn=' + image.img_id
                    facetrack_match['images'].append(url)

                facetrack_matches.append(facetrack_match)
                
            context['data'] = {
                'person_id': person_id,
                'matches': facetrack_matches
            }
	else:
            context['status'] = -1
            context['message'] = u'Person匹配Facetrack失败，请联系管理员！'

    return HttpResponse(json.dumps(context), content_type="application/json")

@csrf_exempt
def addFacetrack2Person(request, task_id):
    context = {}
    if request.method == 'POST':
        data = json.loads(request.POST.get('data'))
        task = TaskInfo.objects.get(id = task_id)

	payload = {
	    "id": 1,
	    "jsonrpc": "2.0",
	    "method": "addfacetracktoperson",
	    "params": {
	        "appkey": task.task_model.model_key,
	        "id_facetrack": data['facetrack_id'],
                "id_person": data['person_id']
	    }
	}
	response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
        if response['result']['code'] <> 0:
            context['status'] = 0
            context['message'] = u'添加FaceTrack到Person失败, 请联系系统管理员！'
        else:
            facetrack = FaceTrack.objects.get(facetrack_id=data["facetrack_id"])
            if facetrack.user_id <> request.user.id:
                context['status'] = -2
                context['message'] = u'操作超时'
            else:
                facetrack.status = 2
                facetrack.person_id = data['person_id']
                facetrack.allocated_time = datetime.now()
                facetrack.finished_time = datetime.now()
                facetrack.save()
                context['status'] = 0
                context['message'] = 'success'
    else:
        context['status'] = -1
        context['message'] = u'请求无效'
    return HttpResponse(json.dumps(context), content_type="application/json")

@csrf_exempt
def addFacetrack2NewPerson(request, task_id):
    context = {}
    context['status'] = 0
    context['message'] = 'success'
    if request.method == 'POST':
        data = json.loads(request.POST.get('data'))
        pid = str(uuid.uuid1())
        task = TaskInfo.objects.get(id = task_id)

        person = Person(pid=pid, model_id=task.task_model_id, name=data['name'], gender=data['gender'], age=data['age'])
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "createperson_id",
            "params": {
                "appkey": task.task_model.model_key,
                "id": pid,
                "info": {"sex": int(data['gender'])}
            }
        }
        response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
        if response['result']['code'] <> 0:
            messages.add_message(request, messages.INFO, u'创建人物失败，请联系系统管理员！')
        else:
            person.save()

	payload = {
	    "id": 1,
	    "jsonrpc": "2.0",
	    "method": "addfacetracktoperson",
	    "params": {
	        "appkey": task.task_model.model_key,
	        "id_facetrack": data['facetrack_id'],
                "id_person": pid
	    }
	}
	response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
        if response['result']['code'] <> 0:
            context['status'] = 0
            context['message'] = u'添加FaceTrack到Person失败, 请联系系统管理员！'
        else:
            facetrack = FaceTrack.objects.get(facetrack_id=data["facetrack_id"])
            if facetrack.user_id <> request.user.id:
                context['status'] = -2
                context['message'] = u'操作超时'
            else:
                facetrack.status = 2
                facetrack.person_id = pid
                facetrack.allocated_time = datetime.now()
                facetrack.finished_time = datetime.now()
                facetrack.isnewlycreated = 1
                facetrack.save()
                context['data'] = {}
                context['data']['person_id'] = pid
    else:
        context['status'] = -1
        context['message'] = u'请求无效'
    return HttpResponse(json.dumps(context), content_type="application/json")

@csrf_exempt
def deleteFacetrackImg(request, task_id):
    context = {}
    if request.method == 'POST':
        data = json.loads(request.POST.get('data'))
	imgid = data['imgurl'][data['imgurl'].find('fn=')+3:]

        facetrack_image = FaceTrackImage.objects.get(img_id = imgid)
        facetrack_image.isdeleted = 1
        facetrack_image.save()

        context['status'] = 0
        context['message'] = u'删除图片成功！'
    else:
        context['status'] = -1
        context['message'] = u'请求无效'
    return HttpResponse(json.dumps(context), content_type="application/json")

@csrf_exempt
def deleteFacetrack(request, task_id):
    context = {}
    if request.method == 'POST':
        data = json.loads(request.POST.get('data'))
        task = TaskInfo.objects.get(id = task_id)

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "deletefacetrack",
            "params": {
                "appkey": task.task_model.model_key,
                "id": data['facetrack_id']
            }
        }
        response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
        if response['result']['code'] <> 0:
            facetrack = FaceTrack.objects.get(facetrack_id=data["facetrack_id"])
            facetrack.status = 2
            facetrack.isdeleted = 1
            facetrack.finished_time = datetime.now()
            facetrack.save()
            context['status'] = -1
            context['message'] = '删除FaceTrack失败，请联系系统管理员！'
        else:
            facetrack = FaceTrack.objects.get(facetrack_id=data["facetrack_id"])
            facetrack.status = 2
            facetrack.isdeleted = 1
            facetrack.finished_time = datetime.now()
            facetrack.save()
            context['status'] = 0
            context['message'] = 'success'
    else:
        context['status'] = -1
        context['message'] = u'请求无效'
    return HttpResponse(json.dumps(context), content_type="application/json")

@csrf_exempt
def addFacetracks2Person(request, task_id):
    context = {}
    context['status'] = 0
    context['message'] = 'success'

    if request.method == 'POST':
        data = json.loads(request.POST.get('data'))
        task = TaskInfo.objects.get(id = task_id)

        for record in data['matches']:
            if record['status'] == 1:
	        payload = {
	            "id": 1,
	            "jsonrpc": "2.0",
	            "method": "addfacetracktoperson",
	            "params": {
	                "appkey": task.task_model.model_key,
	                "id_facetrack": record['id'],
                        "id_person": data['person_id']
	            }
	        }
	        response = requests.post(task.task_model.model_url, data=json.dumps(payload), headers=json.loads(task.task_model.model_headers)).json()
                if response['result']['code'] == 0 and request.user.id is not None:
                    facetrack = FaceTrack.objects.get(facetrack_id=record['id'])
                    facetrack.user_id = request.user.id
                    facetrack.person_id = data['person_id']
                    facetrack.status = 2
                    facetrack.allocated_time = datetime.now()
                    facetrack.finished_time = datetime.now()
                    facetrack.save()
                elif response['result']['code'] == 1:
                    pass
                else:
                    context['status'] = -1
                    context['message'] = u'添加FaceTrack到Person失败，请联系系统管理员！'
    else:
        context['status'] = -1
        context['message'] = u'请求无效'
    return HttpResponse(json.dumps(context), content_type="application/json")

@login_required(login_url='/usercenter/login')
def log(request):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/log')

    facetrack_list = FaceTrack.objects.filter(user_id=request.user.id, status=2, isdeleted=0).order_by('-finished_time')
    keyword = request.GET.get('q')
    if keyword and keyword.isdigit():
        facetrack_list = facetrack_list.filter(task_id=int(keyword))
    elif keyword and len(keyword) == 36:
        facetrack_list = facetrack_list.filter(facetrack_id=keyword.encode('utf-8'))
    else:
        keyword = ''
        pass

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
            'query': keyword,
            'query_num': len(facetrack_list)}
    return render(request, 'usercenter/log.html', context)

@login_required(login_url='/usercenter/login')
def changePerson(request, person_id):
    if len(person_id) >= 16:
        person = get_object_or_404(Person, pid=person_id)
    else:
        person = get_object_or_404(Person, id=person_id)

    if request.method == 'POST':
        person.name = request.POST.get('name')
        person.gender = request.POST.get('gender')
        person.age = request.POST.get('age')
        person.remark = request.POST.get('remark')
        person.save()
        messages.add_message(request, messages.INFO, u'人物信息保存成功！')
        return redirect('/usercenter/person/' + person_id + '/change')

    context = {'person': person}
    return render(request, 'usercenter/changeperson.html', context)

@login_required(login_url='/usercenter/login')
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
            facetrack_imgs = facetrack_object.facetrackimage_set.filter(isdeleted=0)[:30]
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
    return render(request, 'usercenter/viewpersonfacetrack.html', context)

@login_required(login_url='/usercenter/login')
def deletePersonFacetrack(request, person_id):
    facetrack_id = request.GET.get('facetrack_id')
    person = get_object_or_404(Person, id=person_id)

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "cancelfacetrackfromperson",
        "params": {
            "appkey": person.model.model_key,
            "id_facetrack": facetrack_id
        }
    }
    response = requests.post(person.model.model_url, data=json.dumps(payload), headers=json.loads(person.model.model_headers)).json()
    if response['result']['code'] <> 0:
        messages.add_message(request, messages.INFO, u'删除FaceTrack序列失败，请联系系统管理员！')
        return redirect('/usercenter/person/' + person_id + '/facetrack')
    else:
        facetrack = FaceTrack.objects.get(facetrack_id=facetrack_id)
        facetrack.isdeleted = 1
        facetrack.save()
        messages.add_message(request, messages.INFO, u'删除FaceTrack序列成功！')
        return redirect('/usercenter/person/' + person_id + '/facetrack')

@login_required(login_url='/usercenter/login')
def statistics(request):
    apiid = request.GET.get("apiid")
    query = 'select date(finished_time) as finished_date, count(*) FROM facetrack where user_id = ' \
        + str(request.user.id) + ' and to_days(now()) - to_days(finished_time) <= 20 group by finished_date'
    
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

@login_required(login_url='/usercenter/login')
def question(request):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/question')

    question_list = Question.objects.order_by('-created_time')

    page = request.GET.get('page', 1)
    paginator = Paginator(question_list, 20)
    try:
        page = int(page)
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = []

    if page >= 5:
        page_range = list(paginator.page_range)[page-5: page+4]
    else:
        page_range = list(paginator.page_range)[0: page+4]

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now,
            'page_range': page_range,
            'questions': questions,
            'query_num': len(question_list)}
    return render(request, 'usercenter/question.html', context)

@login_required(login_url='/usercenter/login')
def addQuestion(request):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/question')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        user_id = request.user.id
        question = Question(title=title, description=description, user_id=user_id)
        question.save()
        messages.add_message(request, messages.INFO, u'问题发布成功！')
        return redirect('/usercenter/question')

    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now}
    return render(request, 'usercenter/addquestion.html', context)

@login_required(login_url='/usercenter/login')
def showQuestion(request, question_id):
    site_info = SiteInfo.objects.first()
    menu_list = Menu.objects.order_by('order')
    menu_now = get_object_or_404(Menu, link='/usercenter/question')

    question = Question.objects.get(id=question_id)
    question.view_num += 1
    question.save()

    comments_list = question.questioncomment_set.order_by('created_time')
    context = {'site_info': site_info, 
            'menu_list': menu_list,
            'menu_now': menu_now,
            'question': question,
            'comments': comments_list}
    return render(request, 'usercenter/showquestion.html', context)

@login_required(login_url='/usercenter/login')
def addComment(request, question_id):
    comment = request.POST.get("comment")
    user = request.user

    if not comment:
        messages.add_message(request, messages.INFO, u'评论内容不能为空！')
        return redirect('/usercenter/question/' + question_id)

    if len(comment.strip()) < 5:
        messages.add_message(request, messages.INFO, u'评论内容过短！')
        return redirect('/usercenter/question/' + question_id)

    question_comment = QuestionComment()
    question_comment.question = Question.objects.get(id=question_id)
    question_comment.comment = comment
    question_comment.user = user
    question_comment.save()

    return redirect('/usercenter/question/' + question_id)

