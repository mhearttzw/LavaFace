# -*- coding: utf-8 -*-

import base64
import os
import json
import urllib2
import uuid
import datetime
import requests
import sys

from datetime import datetime, timedelta

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

from tasks.models import *

def showImage(request):
    if request.method == 'GET':
        image_type = request.GET.get('type')
        id = request.GET.get('id')
        fn = request.GET.get('fn')

        facetrack = FaceTrack.objects.get(facetrack_id=id)
        facetrack_image = FaceTrackImage.objects.get(facetrack_id=facetrack.id, img_id=fn)
        return HttpResponse(base64.decodestring(facetrack_image.img_base64), content_type='image/jpeg')
    else:
        print('Method not supported!')

