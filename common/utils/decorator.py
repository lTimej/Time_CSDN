from flask import g,current_app
from caches.users import UserStatusCache

def login_required(func):
    '''
    登录装饰器
    :param func: 被判断函数是否已登录
    :return:
    '''
    def wrapper(*args,**kwargs):
        user_id = g.user_id
        is_refresh = g.is_refresh
        if user_id is not None and is_refresh is False:
            return func(*args,**kwargs)
        else:
            return {'message': 'Invalid token'}, 401
    return wrapper

def is_login(func):
    '''
    用户登录，验证是否存在，没登陆，则放行
    :param func:
    :return:
    '''
    def wrapper(*args,**kwargs):
        user_id = g.user_id
        if user_id:
            res = UserStatusCache(user_id).get()
            if not res:
                return {'message': 'User denied'}, 403
        return func(*args,**kwargs)
    return wrapper

