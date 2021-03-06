import base64
import datetime
import re
import imghdr
from models.user import UserProfile
from utils.md5_pwd import encrypt
from caches import users as user_cache
from caches import articles as article_cache


def mobile(str_mobile):
    '''
    手机号验证
    :param str_mobile: 前端传来的数据
    :return:
    '''
    if not re.match(r'^1[3-9]\d{9}$',str_mobile):
        raise ValueError('{} is a invalid mobile'.format(str_mobile))
    else:
        return str_mobile

def regex(pattern):
    '''
    正则匹配验证，模板
    :param str_sms_code:
    :return:
    '''
    def validate(strs):
        '''
        内容验证
        :param strs:
        :return:
        '''
        if not re.match(pattern,strs):
            raise ValueError('{} is invalid'.format(strs))
        else:
            return strs
    return validate

def checkout_img(value):
    '''
    图片验证
    :param value:
    :return:
    '''
    print(11111,value)
    try:
        file_type = imghdr.what(value)
    except Exception:
        raise ValueError('invalid image')
    if not file_type:
        raise ValueError('invalid image')
    else:
        return value

def image_base64(value):
    """
    检查是否是base64图片文件
    :param value:
    :return:
    """
    try:
        photo = base64.b64decode(value)
        file_header = photo[:32]
        file_type = imghdr.what(None, file_header)
    except Exception:
        raise ValueError('Invalid image.')
    else:
        if not file_type:
            raise ValueError('Invalid image.')
        else:
            return photo

def checkout_gender(value):
    '''
    性别验证
    :param value:
    :return:
    '''
    try:
        value = int(value)
    except Exception:
        raise ValueError('invalid value')
    if value in [UserProfile.GENDER.MALE,UserProfile.GENDER.FEMALE]:
        return value
    else:
        raise ValueError('invalid value')

def checkout_date(value):
    '''
    生日、日期验证
    :param value:
    :return:
    '''
    try:
        if not value:
            return value
        _date = datetime.datetime.strptime(value,'%Y-%m-%d')
    except Exception:
        raise ValueError('Invalid date')
    else:
        return _date

def checkout_pwd(value):
    '''
    密码校验
    MD5加密
    :param value:
    :return: 返回加密后的密码
    '''
    text = r'^.{8,16}$'
    if not re.match(text,value):
        raise ValueError('Invalid date')
    else:
        try:
            pwd = encrypt(value)
            return pwd
        except:
            return value

def checkout_username(value):
    '''
    用户名校验
    :param value:
    :return:
    '''
    return value

def checkout_page(value):
    '''
    页码
    :return:
    '''
    try:
        page = int(value)
    except:
        page = 0
    if page<0:
        page = 0
    return page
def checkout_channel_name(value):
    '''
    用户名校验
    :param value:
    :return:
    '''
    if not isinstance(value,str):
        raise ValueError('invalued {}'.format(value))
    return value

def checkout_user_id(value):
    try:
        _user_id = int(value)
    except Exception:
        raise ValueError('Invalid target user id.')
    else:
        if _user_id <= 0:
            raise ValueError('Invalid target user id.')
        else:
            ret = user_cache.UserProfileCache(_user_id).user_is_exist()
            if ret:
                return _user_id
            else:
                raise ValueError('Invalid target user id.')

def checkout_article_id(value):
    print("==================>>>",value,type(value))
    try:
        _aid = int(value)
    except Exception:
        raise  ValueError("Invalid article id")
    else:
        if _aid < 0 :
            raise ValueError("Invalid article id")
        else:
            res = article_cache.ArticlesDetailCache(_aid).exist()
            print(res)
            if res:
                return _aid
            else:
                raise ValueError("Invalid article id")
def checkout_int(value):
    try:
        _id = int(value)
        return _id
    except :
        raise  ValueError("type is error")
