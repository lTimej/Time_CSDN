from flask import request,g
from utils.getJwt import verify_token

def user_authenticate():
    '''
    请求前判断用户是否登录
    :return:
    '''
    #初始化位None
    g.user_id = None
    g.is_refresh = False
    #获取请求头部token
    token = request.headers.get('Authorization')
    #token = Bearer >Dkljdoqijwoi9219239jas.kajsdakh18298jqw.malskji9812u9sa
    #验证token
    if token and token.startswith('Bearer '):
        token = token[7:]
        payload = verify_token((token))
        #存在写入g对象
        if payload:
            g.user_id = payload.get('user_id')
            g.is_refresh = payload.get('is_refresh')