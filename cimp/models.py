from django.db import models

USERTYPE_CHOICE = (
    (1, '管理员'),
    (2, '教师'),
    (3, '学生'),
)
SEX_CHOICE = (
    (1, '男'),
    (2, '女'),
)


class 用户表(models.Model):
    用户名 = models.CharField(max_length=20, unique=True, db_column='用户名')
    密码 = models.CharField(max_length=128, db_column='密码')
    用户类型 = models.PositiveIntegerField(choices=USERTYPE_CHOICE, default='学生', db_column='用户类型')
    性别 = models.PositiveIntegerField(choices=SEX_CHOICE, default='男', db_column='性别')
    真实姓名 = models.CharField(max_length=30, db_index=True, null=True, db_column='真实姓名')
    学号 = models.CharField(max_length=10, null=True)
    手机号 = models.CharField(max_length=11, null=True, db_column='手机号')
    描述 = models.CharField(max_length=1024, null=True, db_column='描述')
    注册时间 = models.DateTimeField(auto_now_add=True, db_column='注册时间')
    最后登录时间 = models.DateTimeField(null=True, db_column='最后登录时间')

    class Meta:
        ordering = ['注册时间']
        db_table = '用户表'


class 校园新闻表(models.Model):
    新闻标题 = models.CharField(max_length=1024, null=True, db_column='新闻标题')
    新闻内容 = models.TextField(null=True, db_column='新闻内容')
    发布时间 = models.DateTimeField(auto_now_add=True, db_column='发布时间')
    最后修改时间 = models.DateTimeField(auto_now=True, db_column='最后修改时间')
    发布人 = models.ForeignKey(to=用户表, on_delete=models.CASCADE, related_name='新闻作者')

    class Meta:
        ordering = ['发布时间']
        db_table = '校园新闻表'


class 校园通知表(models.Model):
    通知标题 = models.CharField(max_length=1024, null=True, db_column='通知标题')
    通知内容 = models.TextField(null=True, db_column='通知内容')
    发布时间 = models.DateTimeField(auto_now=True, db_column='发布时间')
    发布人 = models.ForeignKey(to=用户表, on_delete=models.CASCADE, related_name='通知作者')

    class Meta:
        ordering = ['发布时间']
        db_table = '校园通知表'


STATUS_TYPE = (
    (0, '主题未创建'),
    (1, '主题创建'),
    (2, '主题未通过'),
    (3, '主题通过'),
    (4, '论文创建'),
    (5, '论文未通过'),
    (6, '论文通过'),
)


class 学生论文表(models.Model):
    论文主题 = models.CharField(max_length=1024, null=True, db_column='论文主题')
    主题描述 = models.TextField(null=True, db_column='主题描述')
    论文内容 = models.TextField(null=True, db_column='论文内容')
    论文作者 = models.OneToOneField(to=用户表, limit_choices_to={"用户类型": 3}, on_delete=models.CASCADE,
                                related_name='ArticleAuthor')
    发布时间 = models.DateTimeField(auto_now=True, db_column='发布时间')
    导师 = models.ForeignKey(to=用户表, limit_choices_to={"用户类型": 2}, on_delete=models.CASCADE, related_name='Mentor')
    审核状态 = models.IntegerField(choices=STATUS_TYPE, default='主题未创建', db_column='审核状态')
    论文评分 = models.IntegerField(default=0, db_column='论文评分')

    class Meta:
        db_table = '学生论文表'
        ordering = ['发布时间']


ACTION_TYPE = (
    (1, '主题创建'),
    (2, '主题未通过'),
    (3, '主题通过'),
    (4, '论文创建'),
    (5, '论文未通过'),
    (6, '论文通过'),
    (7, '修改主题'),
    (8, '修改论文'),
)


class 工作流表(models.Model):
    论文 = models.ForeignKey(to=学生论文表, on_delete=models.CASCADE, related_name='ArticleWorkStream')
    论文状态事件 = models.PositiveIntegerField(choices=ACTION_TYPE, null=True)
    事件描述 = models.TextField(null=True)
    事件时间 = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '工作流表'
