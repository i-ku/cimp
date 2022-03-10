# Generated by Django 3.2 on 2021-06-09 00:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cimp', '0002_auto_20210609_0011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='学生论文表',
            name='主题描述',
            field=models.TextField(db_column='主题描述', null=True),
        ),
        migrations.AlterField(
            model_name='学生论文表',
            name='论文主题',
            field=models.CharField(db_column='论文主题', max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='学生论文表',
            name='论文内容',
            field=models.TextField(db_column='论文内容', null=True),
        ),
        migrations.AlterField(
            model_name='校园新闻表',
            name='新闻内容',
            field=models.TextField(db_column='新闻内容', null=True),
        ),
        migrations.AlterField(
            model_name='校园新闻表',
            name='新闻标题',
            field=models.CharField(db_column='新闻标题', max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='校园通知表',
            name='通知内容',
            field=models.TextField(db_column='通知内容', null=True),
        ),
        migrations.AlterField(
            model_name='校园通知表',
            name='通知标题',
            field=models.CharField(db_column='通知标题', max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='用户表',
            name='学号',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='用户表',
            name='手机号',
            field=models.CharField(db_column='手机号', max_length=11, null=True),
        ),
        migrations.AlterField(
            model_name='用户表',
            name='描述',
            field=models.CharField(db_column='描述', max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='用户表',
            name='最后登录时间',
            field=models.DateTimeField(db_column='最后登录时间', null=True),
        ),
        migrations.AlterField(
            model_name='用户表',
            name='真实姓名',
            field=models.CharField(db_column='真实姓名', db_index=True, max_length=30, null=True),
        ),
        migrations.CreateModel(
            name='工作流表',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('论文状态事件', models.PositiveIntegerField(choices=[(1, '主题创建'), (2, '主题未通过'), (3, '主题通过'), (4, '论文创建'), (5, '论文未通过'), (6, '论文通过'), (7, '修改主题'), (8, '修改论文')], null=True)),
                ('事件描述', models.TextField(null=True)),
                ('事件时间', models.DateTimeField(auto_now_add=True)),
                ('论文', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ArticleWorkStream', to='cimp.学生论文表')),
            ],
            options={
                'db_table': '工作流表',
            },
        ),
    ]
