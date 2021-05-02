from flask import g

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