import json

from flask import current_app
from flask_restful import fields,marshal
from redis.exceptions import RedisError
from sqlalchemy.orm import load_only
from sqlalchemy.exc import DatabaseError

from caches import statistics as article_statistics
from caches import users as user_cache

from caches import constants
from models.news import Article
'''
文章缓存
'''

class ArticleInfoCache():
    '''
    article_id
    article_title
    article_content
    article_create_date
    ---------一下统计部分-----------------
    article_like_num
    article_read_num
    article_comment_num
    '''
    article_info = {
        'title':fields.String(attribute='title'),
        'author_id':fields.Integer(attribute='user_id'),
        'pub_date': fields.DateTime(attribute='ctime', dt_format='iso8601'),
        'channel_id': fields.Integer(attribute='channel_id'),
        'allow_comment': fields.Integer(attribute='allow_comment'),
    }
    def __init__(self,article_id):
        self.key = "article:{}:info".format(article_id)
        self.article_id = article_id
        self.redis_conn = current_app.redis_cluster

    def save(self):
        '''
        保存文章信息
        :return:
        '''
        #先从数据库中获取
        try:
            art = Article.query.options(load_only(Article.id,Article.title,Article.user_id,Article.allow_comment,Article.channel_id,Article.ctime)).filter_by(id=self.article_id,status=Article.STATUS.APPROVED).first()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not art:#数据库不存在返回None
            try:
                self.redis_conn.setex(self.key,constants.ArticleNotExistsCacheTTL.get_val(),-1)
            except RedisError as e:
                current_app.logger.error(e)
            return None
        #将数据序列化为特定格式的字典数据
        article_format = marshal(art,self.article_info)
        try:      #setex(key,expire,value)
            self.redis_conn.setex(self.key,constants.ArticleInfoCacheTTL.get_val(),json.dumps(article_format))
        except RedisError as e:
            current_app.logger.error(e)
        return article_format
    def get(self):
        '''
        获取文章信息
        :return:
        '''
        #先从redis中获取
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        #判断是否存在
        if res:
            if res == b'-1':
                return None
            article_dict = json.loads(res)
        else:
            article_dict = self.save()
        article_dict = self.addFields(article_dict)
        return article_dict

    def addFields(self,article_dict):
        '''
        增加字段
        :param article_dict:
        :return:
        '''
        article_dict['article_id'] = self.article_id
        article_dict['read_num'] = article_statistics.ArticleReadCount.get(self.article_id)
        author = user_cache.UserProfileCache(article_dict.get("author_id")).get()
        article_dict['author'] = author.get('user_name')
        article_dict['comment_num'] = article_statistics.ArticleCommentCount.get(self.article_id)
        article_dict['like_num'] = article_statistics.ArticleLikeCount.get(self.article_id)
        article_dict['collection_num'] = article_statistics.ArticleCollectionCount.get(self.article_id)
        return article_dict

    def exist(self):
        '''
        判断文章是否存在
        :return:
        '''
        try:#从缓存中获取
            res = self.redis_conn.get(self.key)
        except RedisError as e:#不存在设置位None
            current_app.logger.error(e)
            res = None
        if not res:#不存在，从数据库中获取
            ret = self.save()
            if ret:
                return True
            else:
                return False
        else:#存在先判断是否为-1
            if res == b'-1':
                return False
            else:
                return True



