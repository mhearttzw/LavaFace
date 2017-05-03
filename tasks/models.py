# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models

from django.conf import settings
from django.utils.timesince import timesince

class TaskStatus(models.Model):
    status_description = models.CharField(u'状态信息', max_length=200, blank=True)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True, null=True)

    class Meta:
        db_table = 'task_status'
        verbose_name = u'状态管理'
        verbose_name_plural = u'状态管理'

class TaskInfo(models.Model):
    task_name = models.CharField(u'任务名称', max_length=200)
    task_description = models.TextField(u'任务描述')
    task_keywords = models.CharField(u'关键字', max_length=200, blank=True)
    task_keywords = models.CharField(u'关键字', max_length=200, blank=True)
    task_flag = models.IntegerField(u'是否截取人脸', default=0)
    task_status = models.ForeignKey(TaskStatus, verbose_name=u'任务状态', on_delete=models.CASCADE)
    data_path = models.CharField(u'数据路径', max_length=200, blank=True)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True, null=True)

    class Meta:
        db_table = 'task_info'
        verbose_name = u'任务管理'
        verbose_name_plural = u'任务管理'

    def __str__(self):
        return self.task_name.encode('utf-8')

    def labels_as_list(self):
        return self.task_keywords.split(',')

    def format_time(self):
        timedelta = timesince(self.created_time).split(',')[0]
        if timedelta.find('minute') != -1: 
            minutes = timedelta.split('\xa0')[0]
            if minutes <> '0':
                return minutes + '分钟前'
            else:
                return '刚刚'
        elif timedelta.find('hour') != -1: 
            return timedelta.split('\xa0')[0] + '小时前'
        elif timedelta.find('day') != -1: 
            return timedelta.split('\xa0')[0] + '天前'
        elif timedelta.find('month') != -1: 
            return timedelta.split('\xa0')[0] + '个月前'
        elif timedelta.find('week') != -1: 
            return timedelta.split('\xa0')[0] + '周前'
        elif timedelta.find('year') != -1: 
            return timedelta.split('\xa0')[0] + '年前'
        else:
            return timedelta

    def get_finished_facetracks(self):
        return self.facetrack_set.filter(status=2)

class FaceTrack(models.Model):
    task = models.ForeignKey(TaskInfo, verbose_name=u'任务信息', on_delete=models.CASCADE)
    facetrack_id = models.CharField('人脸跟踪ID', max_length=255, blank=True)
    image_path = models.CharField('图片路径', max_length=255, blank=True)
    descriptor = models.CharField('视频来源', max_length=255, null=True)
    tracking_time = models.DateTimeField(u'跟踪时间', null=True)
    src_id = models.IntegerField(u'摄像头源', null=True)
    image_num = models.IntegerField(u'图片数', default=0)
    user_id = models.IntegerField(u'操作用户', null=True)
    status = models.IntegerField(u'进度', null=True)
    person_id = models.CharField('人物ID', max_length=255, blank=True)
    isdeleted = models.IntegerField(u'删除标记', default=0)
    allocated_time = models.DateTimeField(u'分配时间', null=True)
    finished_time = models.DateTimeField(u'完成时间', null=True)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'facetrack'
        verbose_name = u'人脸跟踪任务单元'
        verbose_name_plural = u'人脸跟踪任务单元'

    def format_time(self):
        timedelta = timesince(self.finished_time).split(',')[0]
        if timedelta.find('minute') != -1: 
            minutes = timedelta.split('\xa0')[0]
            if minutes <> '0':
                return minutes + '分钟前'
            else:
                return '刚刚'
        elif timedelta.find('hour') != -1: 
            return timedelta.split('\xa0')[0] + '小时前'
        elif timedelta.find('day') != -1: 
            return timedelta.split('\xa0')[0] + '天前'
        elif timedelta.find('month') != -1: 
            return timedelta.split('\xa0')[0] + '个月前'
        elif timedelta.find('week') != -1: 
            return timedelta.split('\xa0')[0] + '周前'
        elif timedelta.find('year') != -1: 
            return timedelta.split('\xa0')[0] + '年前'
        else:
            return timedelta

class FaceTrackImage(models.Model):
    img_base64 = models.TextField(u'图片数据')
    img_id = models.CharField(u'图片id', max_length=100, blank=True)
    facetrack = models.ForeignKey(FaceTrack, verbose_name=u'人脸序列', on_delete=models.CASCADE)
    isdeleted = models.IntegerField(u'是否删除', default=0)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True, null=True)

    class Meta:
        db_table = 'facetrack_image'
        verbose_name = u'人脸序列图片表'
        verbose_name_plural = u'人脸序列图片表'

class Person(models.Model):
    pid = models.CharField('人物ID', max_length=255, blank=True)
    name = models.CharField('姓名', max_length=255, blank=True)
    gender = models.IntegerField(u'性别', null=True)
    age = models.IntegerField(u'年龄', null=True)
    remark = models.TextField(u'备注', null=True)
    facetracks_num = models.IntegerField(u'序列数', default = 0)
    merge_flag = models.IntegerField(u'合并标记', default=0)
    isdeleted = models.IntegerField(u'是否删除', default=0)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True)

    class Meta:
        db_table = 'person'
        verbose_name = u'目标人物表'
        verbose_name_plural = u'目标人物表'

class TaskStatistics(models.Model):
    task = models.ForeignKey(TaskInfo, verbose_name=u'任务信息', on_delete=models.CASCADE)
    proc_date = models.DateField(u'任务日期', null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=u'用户')
    facetracks_total = models.IntegerField(u'总序列数', default = 0)
    facetracks_skipped = models.IntegerField(u'跳过序列数', default = 0)
    facetracks_removed = models.IntegerField(u'摘除序列数', default = 0)
    images_viewed = models.IntegerField(u'图片浏览数', default = 0)
    consumed_time = models.IntegerField(u'耗时', null = True)
    work_efficiency = models.FloatField(u'工作效率', null = True)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True)

    class Meta:
        db_table = 'task_statistics'
        verbose_name = u'任务统计信息表'
        verbose_name_plural = u'任务统计信息表'

class Question(models.Model):
    title = models.CharField('问题标题', max_length=255, blank=True)
    description = models.TextField('问题描述', blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=u'用户')
    view_num = models.IntegerField(u'浏览量', default = 0)
    created_time = models.DateTimeField(u'创建时间', auto_now_add=True)

    class Meta:
        db_table = 'question'
        verbose_name = u'用户问题'
        verbose_name_plural = u'用户问题'

    def format_time(self):
        timedelta = timesince(self.created_time).split(',')[0]
        if timedelta.find('minute') != -1: 
            minutes = timedelta.split('\xa0')[0]
            if minutes <> '0':
                return minutes + '分钟前'
            else:
                return '刚刚'
        elif timedelta.find('hour') != -1: 
            return timedelta.split('\xa0')[0] + '小时前'
        elif timedelta.find('day') != -1: 
            return timedelta.split('\xa0')[0] + '天前'
        elif timedelta.find('month') != -1: 
            return timedelta.split('\xa0')[0] + '个月前'
        elif timedelta.find('week') != -1: 
            return timedelta.split('\xa0')[0] + '周前'
        elif timedelta.find('year') != -1: 
            return timedelta.split('\xa0')[0] + '年前'
        else:
            return timedelta

class QuestionComment(models.Model):
    question = models.ForeignKey(Question, verbose_name='问题', on_delete=models.CASCADE)
    comment = models.TextField('评论内容', blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='用户')
    created_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'question_comment'
        verbose_name = '答疑评论'
        verbose_name_plural = '答疑评论'

    def format_time(self):
        timedelta = timesince(self.created_time).split(',')[0]
        if timedelta.find('minute') != -1: 
            minutes = timedelta.split('\xa0')[0]
            if minutes <> '0':
                return minutes + '分钟前'
            else:
                return '刚刚'
        elif timedelta.find('hour') != -1: 
            return timedelta.split('\xa0')[0] + '小时前'
        elif timedelta.find('day') != -1: 
            return timedelta.split('\xa0')[0] + '天前'
        elif timedelta.find('month') != -1: 
            return timedelta.split('\xa0')[0] + '个月前'
        elif timedelta.find('week') != -1: 
            return timedelta.split('\xa0')[0] + '周前'
        elif timedelta.find('year') != -1: 
            return timedelta.split('\xa0')[0] + '年前'
        else:
            return timedelta
