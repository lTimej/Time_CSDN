import re


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