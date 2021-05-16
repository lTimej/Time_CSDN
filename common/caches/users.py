import json

from flask import current_app

from sqlalchemy.orm import load_only, contains_eager
from sqlalchemy.exc import DatabaseError

from models.user import User,UserProfile
from models.news import Article, ArticleContent

from . import constants

from redis.exceptions import RedisError

from caches import statistics

class UserCache():
    '''
    用户类缓存  redis集群
    redis:    key:value ------>string类型
              user:user_id:profile:  "{user_id:user_id,}"
    '''
    def __init__(self,user_id):
        '''
        初始化key和用户id
        '''
        self.key = "user:{}:basic:profile".format(user_id)
        self.user_id = user_id
        self.redis_conn = current_app.redis_cluster

    def _save(self):
        '''
        保存缓存
        user_name
        head_photo
        introduce
        career
        year_code
        :return:
        '''
        #1、从数据库中获取
        try:
            user = User.query.join(User.profile).options(load_only(User.name, User.profile_photo, User.introduction, User.code_year),contains_eager(User.profile).load_only(UserProfile.career)).filter(User.id==self.user_id).first()
        except DatabaseError as e:
            #获取失败，抛出异常
            current_app.logger.erroe(e)
            raise e

        if not user:#不存在，返回None，并在redis存入-1
            try:
                self.redis_conn.setex(self.key,constants.UserNotExistsCacheTTL.get_val(),-1)
            except RedisError as e:
                current_app.logger.error(e)
            return None
        else:  #存在，获取，并存入redis
            #构造字典
            user_dict = {
                'user_name':user.name,
                'head_photo':user.profile_photo,
                'introduction':user.introduction,
                'code_year':user.code_year,
                'career':user.profile.career
            }
            #转化位字符串存入redis
            user_str = json.dumps(user_dict)
            try:
                self.redis_conn.setex(self.key,constants.UserProfileCacheTTL.get_val(),user_str)
            except RedisError as e:
                current_app.logger.error(e)
            #返回用户数据
            return user_dict


    def get(self):
        '''
        获取用户缓存
        :return:
        '''
        #1、从缓存中获取
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res:  # 存在直接拿
            '''
            redis缓存：数据库不存在时，默认存个-1,并且数据都是byte字节类型
            '''
            if res == b'-1':#数据库不存在
                return None
            else:
                user_dict = json.loads(res)
                return user_dict

        else:  #不存在，先从数据库取，然后存入redis
            return self._save()

    def clearCache(self):
        '''
        清楚缓存
        :return:
        '''
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def user_is_exist(self):
        '''
        通过缓存判断用户是否存在
        :return:
        '''
        try:#取出缓存
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        #缓存位None，先存入缓存
        if res is None:
            ret = self._save()
            if ret is not None:
                return True
            else:#数据库不在返回None
                return False
        else:#缓存位-1返回False
            if res == b'-1':
                return False
            else:
                return True

class UserProfileCache():
    '''
    用户信息缓存类
    '''
    def __init__(self,user_id):
        '''
        初始化key和用户id
        '''
        self.key = "user:{}:profile".format(user_id)
        self.user_id = user_id
        self.redis_conn = current_app.redis_cluster

    def _save(self,user=None,isCache=False):
        '''
            保存缓存
            user_name
            head_photo
            introduce
            career
            year_code
            :return:
        '''
        # 1、从数据库中获取
        if isCache:#判断是否进行缓存
            exist = False#为True，要进行缓存，exist=False
        else:
            try:
                res = self.redis_conn.get(self.key)
            except RedisError as e:
                current_app.logger.error(e)
                exist = False
            else:
                if res == b'-1':
                    exist = False
                else:
                    exist = True
        if not exist:
            if user is None:
                try:
                    user = User.query.join(User.profile).options(load_only(User.name, User.profile_photo, User.introduction, User.code_year),contains_eager(User.profile).load_only(UserProfile.career)).filter(User.id==self.user_id).first()
                except DatabaseError as e:
                    # 获取失败，抛出异常
                    current_app.logger.erroe(e)
                    raise e

                if not user:  # 不存在，返回None，并在redis存入-1
                    try:
                        self.redis_conn.setex(self.key, constants.UserNotExistsCacheTTL.get_val(), -1)
                    except RedisError as e:
                        current_app.logger.error(e)
                    return None
                else:  # 存在，获取，并存入redis
                    # 构造字典
                    user_dict = {
                        'user_name': user.name,
                        'mobile':user.mobile[0:3] + "****" + user.mobile[7:],
                        'pwd':1 if user.password else 0,
                        'head_photo': user.profile_photo,
                        'introduction': user.introduction,
                        'code_year': user.code_year,
                        'career': user.profile.career
                    }
                    # 转化位字符串存入redis
                    user_str = json.dumps(user_dict)
                    try:
                        self.redis_conn.setex(self.key, constants.UserProfileCacheTTL.get_val(), user_str)
                    except RedisError as e:
                        current_app.logger.error(e)
                    # 返回用户数据
                    return user_dict
            else:
                user_dict = {
                    'user_name': user.name,
                    'mobile': user.mobile[0:3] + "****" + user.mobile[7:],
                    'pwd': 1 if user.password != "" else 0,
                    'head_photo': user.profile_photo,
                    'introduction': user.introduction,
                    'code_year': user.code_year,
                    'career': user.profile.career
                }
                return user_dict

    def get(self):
        '''
        获取用户缓存
        :return:
        '''
        # 1、从缓存中获取
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res:  # 存在直接拿
            '''
            redis缓存：数据库不存在时，默认存个-1,并且数据都是byte字节类型
            '''
            if res == b'-1':  # 数据库不存在
                return None
            else:
                user_dict = json.loads(res)

        else:  # 不存在，先从数据库取，然后存入redis
            user_dict = self._save(isCache=True)
            if user_dict is None:
                return None
        #添加字段
        user_dict = self.add_fields(user_dict)
        #如果没有设置头像，给一个默认头像
        if not user_dict.get('head_photo'):
            user_dict['head_photo'] = constants.DEFAULT_USER_PROFILE_PHOTO
        #头像添加完整地址信息
        user_dict['head_photo'] = current_app.config['FDFS_DOMAIN'] + user_dict.get('head_photo')
        return user_dict

    def add_fields(self,user_dict):
        '''
        增加用户信息
        :param user_dict: 原有user信息
        :return:
        '''
        user_dict['focus'] = statistics.UserFocusCount.get(self.user_id)
        user_dict['fans'] = statistics.UserFansCount.get(self.user_id)
        user_dict['visitor'] = statistics.UserVisitCount.get(self.user_id)
        return user_dict

    def clear(self):
        '''
        清楚缓存
        :return:
        '''
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def user_is_exist(self):
        '''
        通过缓存判断用户是否存在
        :return:
        '''
        try:#取出缓存
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        #缓存位None，先存入缓存
        if res is None:
            ret = self._save()
            if ret is not None:
                return True
            else:#数据库不在返回None
                return False
        else:#缓存位-1返回False
            if res == b'-1':
                return False
            else:
                return True

class UserOtherProfileCache():
    '''
    用户其他信息缓存，eg:生日，性别，标签，地区
    '''
    def __init__(self,user_id):
        self.key = "user:{}:otherProfile".format(user_id)
        self.user_id = user_id
        self.redis_conn = current_app.redis_cluster
    def get(self):
        #从缓存重获取
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if not res:#缓存没有，从数据库获取
            try: #数据库重存在，先存入缓存，然后返回数据
                userProfile = UserProfile.query.options(load_only(UserProfile.birthday,UserProfile.gender,UserProfile.tag,UserProfile.area)).filter_by(id=self.user_id).first()
                userProfile_dict = {
                    'birthday':userProfile.birthday.strftime('%Y-%m-%d') if userProfile.birthday else '',
                    'gender':'男' if userProfile.gender==0 else '女',
                    'tag':userProfile.tag,
                    'area':userProfile.area
                }
                try:
                    self.redis_conn.setex(self.key,constants.UserAdditionalProfileCacheTTL.get_val(),json.dumps(userProfile_dict))
                except RedisError as e:
                    current_app.logger.error(e)
                return userProfile_dict
            except DatabaseError as e:# 数据库没有抛错
                current_app.logger.error(e)
                return {"message":"invalid data"},401
        else:
            userProfile_dict = json.loads(res)
            return userProfile_dict

    def clear(self):
        '''
        清楚其他信息缓存
        :return:
        '''
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class UserStatusCache():
    '''
    用户状态
    '''
    def __init__(self,user_id):
        self.key = "user:status:{}".format(user_id)
        self.user_id = user_id
        self.redis_conn = current_app.redis_cluster

    def get(self):
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        #存在，返回
        if res:
            return res
        #不存在，数据库获取
        try:
            us = User.query.options(load_only(User.status)).filter(User.id==self.user_id).first()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not us:
            return False
        #存入缓存
        try:
            self.redis_conn.setex(self.key,constants.UserStatusCacheTTL.get_val(),us.status)
        except RedisError as e:
            current_app.logger.error(e)
        return us.status
    def clear(self):
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class UserArticleCache():
    '''
    当前用户文章缓存
    '''
    def __init__(self,user_id):
        self.key = "user:article:{}".format(user_id)
        self.user_id = user_id
        self.redis_conn = current_app.redis_cluster

    def save(self,page,page_num):
        '''
        保存
        :param page: 页数
        :param page_num: 每页多少个数据，默认10个
        :return:
        '''
        try:#从数据库中获取
            articles = Article.query.options(load_only(Article.id,Article.ctime)).filter(Article.user_id==self.user_id,Article.status==Article.STATUS.DRAFT).order_by(Article.ctime.desc()).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e

        if not articles:
            return 0,[]
        article_ids = []
        cache = []
        #获取文章id列表
        for article in articles:
            article_ids.append(article.id)
            cache.append(article.ctime.timestamp())
            cache.append(article.id)
        if cache:
            try:#写入缓存
                pl = self.redis_conn.pipeline()#开启管道
                pl.zadd(self.key,*cache)#增加
                pl.expire(self.key,constants.UserArticlesCacheTTL.get_val())#设置过期时间
                result = pl.execute()#执行
                if result[0] and not result[1]:
                    self.redis_conn.delete(self.key)
            except RedisError as e:
                current_app.logger.error(e)
        total_num = len(article_ids)
        #获取指定区间数据
        articleIds = article_ids[(page-1)*page_num:page*page_num]
        return total_num,articleIds

    def get_page(self,page,page_num):
        '''
        获取数据
        :return:
        '''
        #从缓存中获取
        try:
            pl = self.redis_conn.pipeline()
            pl.zcard(self.key)
            pl.zrevrange(self.key,(page-1)*page_num,page*page_num)
            total_num,res = pl.execute()
        except RedisError as e:
            current_app.logger.error(e)
            total_num = 0
            res = []
        if total_num >0:
            return total_num,[int(article_id) for article_id in res]
        # total_num = statistics.UserArticleCount.get(self.user_id)
        # if total_num == 0:
        #     return 0,[]
        #从数据库中获取，并保存缓存
        total_num,articleIds = self.save(page,page_num)
        return total_num,articleIds

    def clear(self):
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def exist(self):
        pass




