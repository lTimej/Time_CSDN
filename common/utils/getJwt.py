import jwt
from flask import current_app

def generate_jwt(payload,expire,secret=None):
    '''
    获取token
    :param payload:负载
    :param expire:过期时间
    :param secret:密钥
    :return:token
    '''
    if not secret:
        secret = current_app.config['JWT_SECRET']
    #构造负载字典数据
    _payload = {'expire':expire}
    #将传过来的数据加入负载
    _payload.update(payload)
    #生成token
    token = jwt.encode(_payload,secret,algorithm='HS256')
    #将二进制转换为字符串类型
    return token.decode()

def verify_token(token,secret=None):
    '''
    token验证
    :param token: token
    :param secret: 密钥
    :return: 用户信息
    '''
    if not secret:
        secret = current_app.config['JWT_SECRET']

    try:#解析token,获取负载信息
        payload = jwt.decode(token,secret,algorithms=['HS256'])
    except jwt.PyJWTError:#不存在返回None
        payload = None

    return payload


