from django.shortcuts import render
from .utils import *
from .captcha import *
import base64
import json
import uuid
from .models import *
import traceback
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage
from datetime import datetime
from random import randint

def 获取验证码(request):
    验证码结果 = gen_random_code()
    验证码图像 = Captcha.instance().generate(验证码结果)
    base64图像 = str(base64.b64encode(验证码图像), 'utf-8')
    验证码id = uuid.uuid1()
    cache.set(验证码id, 验证码结果.lower(), 5*60)    # 有效期为五分钟,验证码统一存储成小写
    return JR({'验证码id': 验证码id, '验证码图像': base64图像})

def 登录(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        用户名 = data.get('用户名')
        密码 = data.get('密码')
        # 开始校验验证码
        验证码识别结果 = data.get('验证码识别结果')
        验证码id = data.get('验证码id')
        验证结果 = 验证码是否正确(验证码id, 验证码识别结果)
        if 验证结果 == 2:
            return JR({'code': 404, 'message': '验证码错误，请重新输入验证码！'})
        elif 验证结果 == 3:
            return JR({'code': 405, 'message': '验证码过期，请在5分钟之内完成登录！'})
        # 结束校验验证码
        if not (用户名 and 密码):
            return JR({'code': 400, 'message': '账号或密码不能为空！'})
        else:
            try:
                user = 用户表.objects.get(用户名=用户名)
                if hash_code(密码) == user.密码:
                    user.最后登录时间 = timezone.now()
                    user.save()
                    return JR({
                        'code': 200, 'message': '登录成功！',
                        'token': get_token(user.id),
                        'id': user.id,
                        '用户名': user.用户名,
                        '用户类型': user.用户类型,
                        '真实姓名': user.真实姓名,
                    })
                else:
                    return JR({'code': 401, 'message': '密码错误！'})
            except 用户表.DoesNotExist:
                return JR({'code': 402, 'message': '用户不存在！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 403, 'message': '登录失败！'})

def 用户管理(request):
    # 注册账号
    if request.method == 'POST':
        data = json.loads(request.body)
        用户名 = data.get('用户名')
        密码 = data.get('密码')
        真实姓名 = data.get('真实姓名')
        性别 = data.get('性别')
        用户类型 = data.get('用户类型')
        学号 = data.get('学号')
        手机号 = data.get('手机号')
        描述 = data.get('描述')
        # 开始校验验证码
        验证码识别结果 = data.get('验证码识别结果')
        验证码id = data.get('验证码id')
        验证结果 = 验证码是否正确(验证码id, 验证码识别结果)
        if 验证结果 == 2:
            return JR({'code': 403, 'message': '验证码错误，请重新输入验证码！'})
        elif 验证结果 == 3:
            return JR({'code': 404, 'message': '验证码过期，请在5分钟之内完成注册！'})
        # 结束校验验证码
        if not (用户名 and 密码 and 用户类型 and 真实姓名):
            return JR({'code': 400, 'message': '请仔细检查必填选项是否写全！'})
        else:
            try:
                用户表.objects.get(用户名=用户名)
                return JR({'code': 401, 'message': '用户已存在，换一个试试！'})
            except 用户表.DoesNotExist:
                try:
                    user = 用户表.objects.create(
                        用户名=用户名,
                        密码=hash_code(密码),
                        真实姓名=真实姓名,
                        性别=性别,
                        用户类型=用户类型,
                        学号=学号,
                        手机号=手机号,
                        描述=描述
                    )
                    return JR({
                        'code': 200, 'message': '注册成功！',
                        'id': user.id,
                        'token': get_token(user.id),
                        '用户名': 用户名,
                        '用户类型': 用户类型,
                    })
                except:
                    print(traceback.format_exc())
                    return JR({'code': 402, 'message': '注册失败！'})
    # 列出账号
    if request.method == 'GET':
        # 只有管理员可以使用此接口获取用户
        token = request.META.get('HTTP_TOKEN')
        userid = is_login(token)
        if userid == 0:
            return JR({'code': 403, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
        用户类型 = 用户表.objects.get(id=userid).用户类型
        if userid == 0 or 用户类型 != 1:
            return JR({'code': 402, 'message': '请使用管理员账户登录！'})

        data = request.GET
        # 判断GET中是否有参数，如果有，按条件返回数据，如果没有，则返回全部数据
        if not data:
            # get 中没有参数，返回全部新闻
            用户列表 = 用户表.objects.values('id', '用户名', '用户类型', '性别', '真实姓名', '学号', '手机号', '描述', '注册时间', '最后登录时间') \
                .order_by('-id')
            return JR({'code': 200, '用户列表': list(用户列表), '用户总数': len(用户列表), 'message': '获取获取列表成功！'})
        else:
            pagesize = int(data.get('pagesize'))
            pageno = int(data.get('pageno'))
            keywords = data.get('keywords')
            # 分页过滤部分
            try:
                # values()获取到全部字段，只需要填写需要的字段即可
                QuerySet对象 = 用户表.objects.values('id', '用户名', '用户类型', '性别', '真实姓名', '学号', '手机号', '描述', '注册时间', '最后登录时间')\
                    .order_by('-id')
                if keywords:
                    # 指定在用户名中查找
                    conditions = [Q(用户名__contains=one) for one in keywords.split(' ') if one]
                    query = Q()
                    for condition in conditions:
                        query &= condition
                    QuerySet对象 = QuerySet对象.filter(query)
                # 使用分页对象，设定每页多少条记录
                page_all = Paginator(QuerySet对象, pagesize)
                # 从数据库中读取数据，指定读取其中第几页
                page_no = page_all.page(pageno)
                # 将 QuerySet 对象 转换成list类型
                用户列表 = list(page_no)
                # total 返回总共有多少个符合条件的用户
                return JR({'code': 200, '用户列表': 用户列表, '用户总数': page_all.count, 'message': '获取用户列表成功！'})
            except EmptyPage:
                return JR({'code': 401, '用户列表': [], '用户总数': 0, 'message': '没有这一页！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 400, 'message': '获取用户失败！'})

def 列出教师(request):
    # 列出所有老师的信息（只有学生都能够查看）
    if request.method == 'GET':
        token = request.META.get('HTTP_TOKEN')
        userid = is_login(token)
        if userid == 0:
            return JR({'code': 401, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
        用户类型 = 用户表.objects.get(id=userid).用户类型
        if 用户类型 != 3:
            return JR({'code': 402, 'message': '只有学生才能查看所有教师真实姓名信息！'})
        try:
            教师列表 = 用户表.objects.filter(用户类型=2).values('id', '用户名', '真实姓名')
            return JR({'code': 200, 'message': '获取教师真实姓名成功！', '教师列表': list(教师列表)})
        except:
            print(traceback.format_exc())
            return JR({'code': 400, 'message': '获取教师信息失败！'})

def 单用户管理(request, no):
    # 管理员可以通过此接口对用户进行查改删，除管理员外用户本人也可以对自己的信息进行查改删操作
    token = request.META.get('HTTP_TOKEN')
    userid = is_login(token)
    if userid == 0:
        return JR({'code': 402, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
    用户类型 = 用户表.objects.get(id=userid).用户类型
    if not (userid == no or 用户类型 == 1):
        return JR({'code': 403, 'message': '请使用管理员账户登录！'})
    else:
        try:
            user = 用户表.objects.get(id=no)
        except 用户表.DoesNotExist:
            return JR({'code': 400, 'message': f'ID为 {no} 的用户不存在！'})
        except:
            print(traceback.format_exc())
            return JR({'code': 401, 'message': '操作失败！'})
        else:
            # 查看一条用户的信息
            if request.method == 'GET':
                return JR({
                    'code': 200,
                    'message': '操作成功！',
                    '用户名': user.用户名,
                    '用户类型': user.用户类型,
                    '真实姓名': user.真实姓名,
                    '性别': user.性别,
                    '学号': user.学号,
                    '手机号': user.手机号,
                    '描述': user.描述,
                    '注册时间': user.注册时间,
                    '最后登录时间': user.最后登录时间
                })
            # 删除一条用户的信息
            if request.method == 'DELETE':
                user.delete()
                return JR({'code': 200, 'message': '操作成功！'})
            # 修改一条用户的信息
            if request.method == 'PUT':
                data = json.loads(request.body)
                # 这里应该预处理，把不能修改的数据从字典中踢出去，防止被人利用此接口修改禁止修改的字段
                # del data['id']

                # 用户名要唯一
                if '用户名' in data:
                    用户名 = data['用户名']
                    if 用户表.objects.filter(用户名=用户名).exists():
                        return JR({'code': 404, 'message': f'用户名为 {用户名} 的用户已经存在！'})
                # 密码处理后要pop出去
                if '密码' in data:
                    user.密码 = hash_code(data.pop('密码'))

                for field, value in data.items():
                    setattr(user, field, value)
                user.save()
                return JR({'code': 200, 'message': '操作成功！'})

def 校园新闻管理(request):
    # 添加新闻      只有管理员或者教师能够添加新闻
    if request.method == 'POST':
        token = request.META.get('HTTP_TOKEN')
        userid = is_login(token)
        if userid == 0:
            return JR({'code': 400, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
        if 用户表.objects.get(id=userid).用户类型 == 3:
            return JR({'code': 401, 'message': '学生不能发布新闻！'})
        else:
            data = json.loads(request.body)
            新闻标题 = data.get('新闻标题')
            新闻内容 = data.get('新闻内容')
            if 新闻标题 and 新闻内容:
                try:
                    news = 校园新闻表(新闻标题=新闻标题, 新闻内容=新闻内容, 发布人_id=userid)
                    news.save()
                    return JR({'code': 200, 'message': '发布新闻成功！', 'id': news.id, 'time': news.发布时间})
                except:
                    print(traceback.format_exc())
                    return JR({'code': 403, 'message': '发布新闻失败！'})
            else:
                return JR({'code': 402, 'message': '新闻标题或正文不能为空！'})
    # 列出新闻      任何人都能够查看列出的新闻
    if request.method == 'GET':
        data = request.GET
        # 判断GET中是否有参数，如果有，按条件返回数据，如果没有，则返回全部数据
        if not data:
            # get 中没有参数，返回全部新闻
            新闻列表 = 校园新闻表.objects.annotate(
                新闻发布人用户名=F('发布人__用户名'), 新闻发布人用户类型=F('发布人__用户类型'), 新闻发布人真实姓名=F('发布人__真实姓名')
            ).values('id', '新闻标题', '新闻内容', '发布时间', '新闻发布人用户名', '新闻发布人真实姓名', '最后修改时间').order_by('-id')
            return JR({'code': 200, '新闻列表': list(新闻列表), '新闻总数': len(新闻列表), 'message': '获取新闻列表成功！'})
        else:
            pagesize = int(data.get('pagesize'))
            pageno = int(data.get('pageno'))
            keywords = data.get('keywords')
            try:
                # values()获取到全部字段，只需要填写需要的字段即可
                QuerySet对象 = 校园新闻表.objects.annotate(
                    新闻发布人用户名=F('发布人__用户名'),
                    新闻发布人用户类型=F('发布人__用户类型'),
                    新闻发布人真实姓名=F('发布人__真实姓名')
                ).values(
                    'id',
                    '新闻标题',
                    '新闻内容',
                    '发布时间',
                    '新闻发布人用户名',
                    '最后修改时间',
                    '新闻发布人用户类型',
                    '新闻发布人真实姓名'
                ).order_by('-id')
                if keywords:
                    # 指定在标题中查找
                    conditions = [Q(新闻标题__contains=one) for one in keywords.split(' ') if one]
                    query = Q()
                    for condition in conditions:
                        query &= condition
                    QuerySet对象 = QuerySet对象.filter(query)

                # 使用分页对象，设定每页多少条记录
                page_all = Paginator(QuerySet对象, pagesize)
                # 从数据库中读取数据，指定读取其中第几页
                page_no = page_all.page(pageno)
                # 将 QuerySet 对象 转换成list类型
                新闻列表 = list(page_no)
                # 新闻总数 返回总共有多少个符合条件的用户
                return JR({'code': 200, '新闻列表': 新闻列表, '新闻总数': page_all.count, 'message': '获取新闻列表成功！'})
            except EmptyPage:
                return JR({'code': 401, 'message': '没有这一页！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 400, 'message': '获取新闻失败！'})

def 单新闻管理(request, no):
    try:
        news = 校园新闻表.objects.get(id=no)
    except 校园新闻表.DoesNotExist:
        return JR({'code': 400, 'message': f'ID为 {no} 的新闻不存在！'})
    except:
        print(traceback.format_exc())
        return JR({'code': 401, 'message': '操作失败！'})
    else:
        # 查看一条新闻    任何人都可以查看新闻
        if request.method == 'GET':
            return JR({
                'code': 200, 'message': '操作成功！',
                '新闻标题': news.新闻标题,
                '新闻内容': news.新闻内容,
                '新闻发布人用户名': news.发布人.用户名,
                '新闻发布人真实姓名': news.发布人.真实姓名,
                '新闻发布人用户类型': news.发布人.用户类型,
                '发布时间': news.发布时间,
                '最后修改时间': news.最后修改时间
            })
        # 修改或删除一条新闻    管理员可以修改或删除，如果我是教师，那么别的教师不能修改或删除我发布的新闻（教师只能修改或删除自己发布的新闻），学生则不能新闻进行修改和删除
        if request.method == 'PUT' or 'DELETE':
            token = request.META.get('HTTP_TOKEN')
            userid = is_login(token)
            # 未登录用户
            if userid == 0:
                return JR({'code': 402, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
            else:
                用户类型 = 用户表.objects.get(id=userid).用户类型
                # 学生用户
                if 用户类型 == 3:
                    return JR({'code': 403, 'message': '学生不能修改或删除新闻！'})
                # 教师用户
                elif 用户类型 == 2:
                    # 如果是教师本人发布的新闻，才可以操作
                    if news.发布人.id == userid:
                        if request.method == 'DELETE':
                            news.delete()
                            return JR({'code': 200, 'message': '删除成功！'})
                        else:
                            data = json.loads(request.body)
                            if '新闻标题' in data:
                                news.新闻标题 = data['新闻标题']
                            if '新闻内容' in data:
                                news.新闻内容 = data['新闻内容']
                            news.save()
                            return JR({'code': 200, 'message': '修改成功！'})
                    else:
                        return JR({'code': 404, 'message': '你不能修改或删除其他教师发布的新闻！'})
                # 管理员用户
                elif 用户类型 == 1:
                    if request.method == 'DELETE':
                        news.delete()
                        return JR({'code': 200, 'message': '删除成功！'})
                    else:
                        data = json.loads(request.body)
                        if '新闻标题' in data:
                            news.新闻标题 = data['新闻标题']
                        if '新闻内容' in data:
                            news.新闻内容 = data['新闻内容']
                        news.save()
                        return JR({'code': 200, 'message': '修改成功！'})

def 校园通知管理(request):
    # 添加通知      只有管理员和教师能够添加通知
    if request.method == 'POST':
        token = request.META.get('HTTP_TOKEN')
        userid = is_login(token)
        if userid == 0:
            return JR({'code': 400, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
        if 用户表.objects.get(id=userid).用户类型 == 3:
            return JR({'code': 401, 'message': '学生不能发布通知！'})
        else:
            data = json.loads(request.body)
            通知标题 = data.get('通知标题')
            通知内容 = data.get('通知内容')
            if 通知标题 and 通知内容:
                try:
                    notice = 校园通知表(通知标题=通知标题, 通知内容=通知内容, 发布人_id=userid)
                    notice.save()
                    return JR({'code': 200, 'message': '发布通知成功！', 'id': notice.id, '发布时间': notice.发布时间})
                except:
                    print(traceback.format_exc())
                    return JR({'code': 403, 'message': '发布通知失败！'})
            else:
                return JR({'code': 402, 'message': '通知标题或正文不能为空！'})
    # 列出通知      任何人都能够查看列出的通知
    if request.method == 'GET':
        data = request.GET
        # 判断GET中是否有参数，如果有，按条件返回数据，如果没有，则返回全部数据
        if not data:
            # get 中没有参数，返回全部通知
            通知列表 = 校园通知表.objects.annotate(
                通知发布人真实姓名=F('发布人__真实姓名'), 通知发布人用户类型=F('发布人__用户类型'), 通知发布人用户名=F('发布人__用户名')
            ).values(
                'id',
                '通知标题',
                '通知内容', '发布时间',
                '通知发布人真实姓名',
                '通知发布人用户类型',
                '通知发布人用户名'
            ).order_by('-id')
            return JR({'code': 200, '通知列表': list(通知列表), '通知总数': len(通知列表), 'message': '获取通知列表成功！'})
        else:
            pagesize = int(data.get('pagesize'))
            pageno = int(data.get('pageno'))
            keywords = data.get('keywords')
            try:
                # values()获取到全部字段，只需要填写需要的字段即可
                QuerySet对象 = 校园通知表.objects.annotate(
                    通知发布人真实姓名=F('发布人__真实姓名'), 通知发布人用户类型=F('发布人__用户类型'), 通知发布人用户名=F('发布人__用户名')
                ).values('id', '通知标题', '通知内容', '发布时间', '通知发布人真实姓名', '通知发布人用户类型', '通知发布人用户名').order_by('-id')
                if keywords:
                    # 指定在标题中查找
                    conditions = [Q(通知标题__contains=one) for one in keywords.split(' ') if one]
                    query = Q()
                    for condition in conditions:
                        query &= condition
                    QuerySet对象 = QuerySet对象.filter(query)

                # 使用分页对象，设定每页多少条记录
                page_all = Paginator(QuerySet对象, pagesize)
                # 从数据库中读取数据，指定读取其中第几页
                page_no = page_all.page(pageno)
                # 将 QuerySet 对象 转换成list类型
                通知列表 = list(page_no)
                # 通知总数 返回总共有多少个符合条件的用户
                return JR({'code': 200, '通知列表': 通知列表, '通知总数': page_all.count, 'message': '获取通知列表成功！'})
            except EmptyPage:
                return JR({'code': 401, 'message': '没有这一页！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 400, 'message': '获取通知失败！'})

def 单通知管理(request, no):
    try:
        notice = 校园通知表.objects.get(id=no)
    except 校园通知表.DoesNotExist:
        return JR({'code': 400, 'message': f'ID为 {no} 的通知不存在！'})
    except:
        print(traceback.format_exc())
        return JR({'code': 401, 'message': '操作失败！'})
    else:
        # 查看一条通知    任何人都可以查看通知
        if request.method == 'GET':
            return JR({
                'code': 200,
                'message': '操作成功！',
                '通知标题': notice.通知标题,
                '通知内容': notice.通知内容,
                '通知发布人真实姓名': notice.发布人.真实姓名,
                '通知发布人用户类型': notice.发布人.用户类型,
                '发布时间': notice.发布时间
            })
        # 修改或删除一条通知    管理员可以修改或删除，如果我是教师，那么别的教师不能修改或删除我发布的通知（教师只能修改或删除自己发布的通知），学生则不能通知进行修改和删除
        if request.method == 'PUT' or 'DELETE':
            token = request.META.get('HTTP_TOKEN')
            userid = is_login(token)
            # 未登录用户
            if userid == 0:
                return JR({'code': 402, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
            else:
                用户类型 = 用户表.objects.get(id=userid).用户类型
                # 学生用户
                if 用户类型 == 3:
                    return JR({'code': 403, 'message': '学生不能修改或删除通知！'})
                # 教师用户
                elif 用户类型 == 2:
                    # 如果是教师本人发布的通知，才可以操作
                    if notice.发布人.id == userid:
                        if request.method == 'DELETE':
                            notice.delete()
                            return JR({'code': 200, 'message': '删除成功！'})
                        else:
                            data = json.loads(request.body)
                            if '通知标题' in data:
                                notice.通知标题 = data['通知标题']
                            if '通知内容' in data:
                                notice.通知内容 = data['通知内容']
                            notice.save()
                            return JR({'code': 200, 'message': '修改成功！'})
                    else:
                        return JR({'code': 404, 'message': '你不能修改或删除其他教师发布的通知！'})
                # 管理员用户
                elif 用户类型 == 1:
                    if request.method == 'DELETE':
                        notice.delete()
                        return JR({'code': 200, 'message': '删除成功！'})
                    else:
                        data = json.loads(request.body)
                        if '通知标题' in data:
                            notice.通知标题 = data['通知标题']
                        if '通知内容' in data:
                            notice.通知内容 = data['通知内容']
                        notice.save()
                        return JR({'code': 200, 'message': '修改成功！'})

def 列出论文(request):
    # 列出论文      任何人都能够查看列出的论文
    if request.method == 'GET':
        data = request.GET
        # 判断GET中是否有参数，如果有，按条件返回数据，如果没有，则返回全部数据
        if not data:
            # get 中没有参数，返回全部论文
            论文列表 = 学生论文表.objects.annotate(
                论文作者真实姓名=F('论文作者__真实姓名'),
                导师真实姓名=F('导师__真实姓名'),
            ).values(
                'id',
                '论文主题',
                '论文内容',
                '论文作者真实姓名',
                '导师真实姓名',
                '发布时间',
                '论文评分'
            ).filter(审核状态=6).order_by('-id')
            return JR({'code': 200, '论文总数': len(论文列表), 'message': '获取论文列表成功！', '论文列表': list(论文列表)})
        else:
            pagesize = int(data.get('pagesize'))
            pageno = int(data.get('pageno'))
            keywords = data.get('keywords')
            try:
                # values()获取到全部字段，只需要填写需要的字段即可
                QuerySet对象 = 学生论文表.objects.annotate(
                    论文作者真实姓名=F('论文作者__真实姓名'),
                    导师真实姓名=F('导师__真实姓名'),
                ).values(
                    'id',
                    '论文主题',
                    '论文内容',
                    '论文作者真实姓名',
                    '导师真实姓名',
                    '发布时间',
                    '论文评分'
                ).filter(审核状态=6).order_by('-id')
                if keywords:
                    # 指定在用户名中查找
                    conditions = [Q(论文主题__contains=one) for one in keywords.split(' ') if one]
                    query = Q()
                    for condition in conditions:
                        query &= condition
                    QuerySet对象 = QuerySet对象.filter(query)
                # 使用分页对象，设定每页多少条记录
                page_all = Paginator(QuerySet对象, pagesize)
                # 从数据库中读取数据，指定读取其中第几页
                page_no = page_all.page(pageno)
                # 将 QuerySet 对象 转换成list类型
                论文列表 = list(page_no)
                # 论文总数 返回总共有多少个符合条件的用户
                return JR({'code': 200, '论文总数': page_all.count, 'message': '获取论文列表成功！', '论文列表': 论文列表})
            except EmptyPage:
                return JR({'code': 401, 'message': '没有这一页！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 400, 'message': '获取论文失败！'})

def 单论文管理(request, no):
    # 已经通过审批的论文，不允许再次修改
    # 查看一篇论文
    if request.method == 'GET':
        try:
            article = 学生论文表.objects.get(id=no)
            return JR({
                'code': 200,
                'message': '操作成功！',
                '论文主题': article.论文主题,
                '论文内容': article.论文内容,
                '论文作者': article.论文作者.真实姓名,
                '导师': article.导师.真实姓名,
                '论文评分': article.论文评分,
                '发布时间': article.发布时间
            })
        except:
            print(traceback.format_exc())
            return JR({'code': 400, 'message': '操作失败！'})
    # 删除一篇论文
    if request.method == 'DELETE':
        token = request.META.get('HTTP_TOKEN')
        userid = is_login(token)
        if userid == 0:
            return JR({'code': 400, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
        usertype = 用户表.objects.get(id=userid).用户类型
        if usertype != 1:
            return JR({'code': 401, 'message': '只有管理员能够删除论文！'})
        try:
            学生论文表.objects.get(id=no).delete()
            return JR({'code': 200, 'message': '删除成功！'})
        except:
            print(traceback.format_exc())
            return JR({'code': 402, 'message': '删除失败！'})

def 工作流管理(request):
    token = request.META.get('HTTP_TOKEN')
    userid = is_login(token)
    if userid == 0:
        return JR({'code': 400, 'message': '未登录或身份认证已过期，请重新登录后再试！'})
    user = 用户表.objects.get(id=userid)

    # 列出工作流      只有学生都能够查看
    if request.method == 'GET':
        if user.用户类型 != 3:
            return JR({'code': 402, 'message': '只有学生才能查看论文工作流！'})
        try:
            article = user.ArticleAuthor
            工作流列表 = article.ArticleWorkStream.values('论文状态事件', '事件描述', '事件时间')
            return JR({
                'code': 200,
                'message': '获取工作流成功！',
                '审核状态': article.审核状态,
                '工作流列表': list(工作流列表),
                '论文主题': article.论文主题,
                '主题描述': article.主题描述,
                '论文内容': article.论文内容,
                '论文评分': article.论文评分,
                '导师': article.导师.真实姓名
            })
        except 学生论文表.DoesNotExist:
            return JR({'code': 200, 'message': '获取工作流成功！', '审核状态': 0})
        except:
            print(traceback.format_exc())
            return JR({'code': 401, 'message': '获取工作流失败！'})

    # 创建/修改工作流
    if request.method == 'POST':
        data = json.loads(request.body)
        论文状态事件 = data.get('论文状态事件')

        # 创建主题
        if 论文状态事件 == 1:
            if user.用户类型 != 3:
                return JR({'code': 401, 'message': '只有学生才能创建主题！'})
            论文主题 = data.get('论文主题')
            主题描述 = data.get('主题描述')
            导师id = data.get('导师id')
            if 论文主题 and 导师id:
                try:
                    article = 学生论文表.objects.create(
                        论文主题=论文主题,
                        主题描述=主题描述,
                        论文作者_id=userid,
                        导师_id=导师id,
                        审核状态=1
                    )
                    工作流表.objects.create(论文=article, 论文状态事件=1, 事件描述=主题描述)
                    return JR({'code': 200, 'message': '主题创建成功！'})
                except:
                    print(traceback.format_exc())
                    return JR({'code': 403, 'message': '主题创建失败！'})
            else:
                return JR({'code': 402, 'message': '主题或导师不能为空！'})
        # 创建论文
        if 论文状态事件 == 4:
            if user.用户类型 != 3:
                return JR({'code': 401, 'message': '只有学生才能创建论文！'})
            论文内容 = data.get('论文内容')
            try:
                article = user.ArticleAuthor
                article.论文内容 = 论文内容
                article.审核状态 = 4
                article.save()
                工作流表.objects.create(论文=article, 论文状态事件=4, 事件描述=论文内容)
                return JR({'code': 200, 'message': '创建论文成功！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 402, 'message': '创建论文失败！'})
        # 修改主题
        if 论文状态事件 == 7:
            if user.用户类型 != 3:
                return JR({'code': 401, 'message': '只有学生才能修改论文主题！'})
            论文主题 = data.get('论文主题')
            主题描述 = data.get('主题描述')
            try:
                article = user.ArticleAuthor
                article.论文主题 = 论文主题
                article.主题描述 = 主题描述
                article.审核状态 = 1
                article.save()
                工作流表.objects.create(论文=article, 论文状态事件=7, 事件描述=主题描述)
                return JR({'code': 200, 'message': '修改论文主题成功！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 402, 'message': '修改论文主题失败！'})
        # 修改论文
        if 论文状态事件 == 8:
            if user.用户类型 != 3:
                return JR({'code': 401, 'message': '只有学生才能修改论文！'})
            论文内容 = data.get('论文内容')
            try:
                article = user.ArticleAuthor
                article.论文内容 = 论文内容
                article.审核状态 = 4
                article.save()
                工作流表.objects.create(论文=article, 论文状态事件=8, 事件描述=论文内容)
                return JR({'code': 200, 'message': '修改论文成功！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 402, 'message': '修改论文失败！'})
        # 驳回或通过 主题/论文
        if 论文状态事件 in [2, 3, 5, 6]:
            if user.用户类型 != 2:
                return JR({'code': 401, 'message': '只有教师才能审批！'})
            事件描述 = data.get('事件描述')
            id = data.get('id')
            论文评分 = data.get('论文评分') if 论文状态事件 == 6 else 0
            try:
                article = 学生论文表.objects.get(id=id)
                article.审核状态 = 论文状态事件
                article.论文评分 = 论文评分
                article.save()
                工作流表.objects.create(论文_id=id, 论文状态事件=论文状态事件, 事件描述=事件描述)
                return JR({'code': 200, 'message': '操作成功！'})
            except:
                print(traceback.format_exc())
                return JR({'code': 402, 'message': '操作失败！'})

def 获取待审批主题(request):
    if request.method == 'GET':
        token = request.META.get('HTTP_TOKEN')
        userid = is_login(token)
        if userid == 0:
            return JR({'code': 400, 'message': '未登录或身份认证已过期！'})
        user = 用户表.objects.get(id=userid)
        if user.用户类型 != 2:
            return JR({'code': 401, 'message': '只有教师才能审批论文！'})
        try:
            所有待审批论文主题 = 学生论文表.objects.filter(审核状态=1)
            if 所有待审批论文主题.exists():
                一个待审批主题 = 所有待审批论文主题.first()
                return JR({
                    'code': 200,
                    'message': '操作成功！',
                    'total': 所有待审批论文主题.count(),
                    'id': 一个待审批主题.id,
                    '论文主题': 一个待审批主题.论文主题,
                    '主题描述': 一个待审批主题.主题描述
                })
            else:
                return JR({'code': 200, 'message': '操作成功！', 'total': 0})
        except:
            print(traceback.format_exc())
            return JR({'code': 402, 'message': '获取待审批主题失败！'})

def 获取待审批论文(request):
    if request.method == 'GET':
        token = request.META.get('HTTP_TOKEN')
        userid = is_login(token)
        if userid == 0:
            return JR({'code': 400, 'message': '未登录或身份认证已过期！'})
        user = 用户表.objects.get(id=userid)
        if user.用户类型 != 2:
            return JR({'code': 401, 'message': '只有教师才能审批论文！'})
        try:
            所有待审批论文 = 学生论文表.objects.filter(审核状态=4)
            if 所有待审批论文.exists():
                一个待审批论文 = 所有待审批论文.first()
                return JR({
                    'code': 200,
                    'message': '操作成功！',
                    'total': 所有待审批论文.count(),
                    'id': 一个待审批论文.id,
                    '论文主题': 一个待审批论文.论文主题,
                    '论文内容': 一个待审批论文.论文内容
                })
            else:
                return JR({'code': 200, 'message': '操作成功！', 'total': 0})
        except:
            print(traceback.format_exc())
            return JR({'code': 402, 'message': '获取待审批论文失败！'})

def echarts图表接口(request):
    if request.method == 'GET':
        return JR({
            '论文数量': 学生论文表.objects.filter(审核状态=6).count(),
            '新闻数量': 校园新闻表.objects.count(),
            '通知数量': 校园通知表.objects.count()
        })

def upload(request):
    '''
    上传单文件的实例如下
    uploadfile = request.FILES['upload']
    其中'upload'需要与前端设置的上传文件名一致
    '''

    # 以下是上传多个文件的实例
    # data 是一个数组，返回图片Object
    # Object中包含需要包含url、alt和href三个属性,它们分别代表图片地址、图片文字说明和跳转链接
    # alt和href属性是可选的，可以不设置或设置为空字符串,需要注意的是url是一定要填的。

    # if len(request.FILES) > 9:
    #     return JR({'code': 400, 'message': '上传图片不能超过9张！'})
    data = []
    for uploadfile in request.FILES.values():
        filetype = uploadfile.name.split('.')[-1]

        # if uploadfile.size > 5*1024*1024:
        #     return JR({'code': 400, 'message': '图片大小不能大于5M！'})
        # if filetype not in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        #     return JR({'code': 400, 'message': '图片格式只能是jpg，jpeg，png，gif，bmp之中的一种！'})

        suffix = datetime.now().strftime('%Y%m%d%H%M%S_') + str(randint(0, 999999))
        filename = f'id_{suffix}.{filetype}'

        # 写入文件到静态文件访问区，wb代表二进制
        with open(fr'{settings.UPLOAD_ROOT}/{filename}', 'wb') as f:
            # 读取上传文件数据
            bytes = uploadfile.read()
            # 写入文件
            f.write(bytes)

        data.append({'url': f'/upload/{filename}', 'alt': '', 'href': ''})

    return JR({'errno': 0, 'data': data})
