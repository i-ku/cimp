import jwt
from jwt import InvalidTokenError, ExpiredSignatureError, DecodeError
import datetime
from django.utils import timezone
from django.conf import settings
import hashlib
import random
from django.http import JsonResponse
from django.core.cache import cache


def hash_code(s, salt=settings.SECRET_KEY):  # 加点盐
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()


ALL_CHARS = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def gen_random_code(length=4):
    """生成指定长度的随机验证码"""
    return ''.join(random.choices(ALL_CHARS, k=length))


def 验证码是否正确(验证码id, 验证码识别结果):
    """验证码正确返回1，错误返回2，过期返回3"""
    if cache.has_key(验证码id):
        if cache.get(验证码id) == 验证码识别结果.lower():
            return 1  # 验证码正确
        else:
            return 2  # 验证码错误
    else:
        return 3  # 验证码不存在,说明验证码已经过期


def JR(data, *args, **kwargs):
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False}, *args, **kwargs)


def get_token(userid):
    payload = {
        'exp': timezone.now() + datetime.timedelta(days=1),
        'userid': userid
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def get_id(token):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])['userid']
    except (ExpiredSignatureError, InvalidTokenError, DecodeError):
        return 0


def is_login(token):
    if not token:
        return 0    # 对应token是None或''的情况
    else:
        if token == 'undefined':
            return 0
        else:
            return get_id(token)
