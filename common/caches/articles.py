import json

from flask import current_app,g
from flask_restful import fields,marshal
from redis.exceptions import RedisError
from sqlalchemy.orm import load_only,contains_eager
from sqlalchemy.exc import DatabaseError

from caches import statistics as article_statistics
from caches import users as user_cache

from caches import constants
from models.news import Article,ArticleContent,Attitude,CommentLiking
'''
文章缓存
'''

class ArticleInfoCache():
    '''
    根据文章id
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
    def clear(self):
        '''
        清除缓存
        :return:
        '''
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class ChannelArticleCache():
    '''
    根据文章频道:获取文章id
    '''
    def __init__(self,channel_id):
        self.key = "channel:article:{}".format(channel_id)
        self.channel_id = channel_id
        self.redis_conn = current_app.redis_cluster

    def get_page_content(self,page,page_num):
        #从缓存中获取
        try:
            pl = self.redis_conn.pipeline()
            #当 key 存在且是有序集类型时，返回有序集的基数。
            pl.zcard(self.key)
            #返回有序集 key 中，指定区间内的成员
            pl.zrevrange(self.key,(page-1)*page_num,page*page_num)
            total_num,res = pl.execute()#res = [b'4', b'51', b'54', b'55', b'8', b'6', b'9', b'59', b'10', b'52', b'57']
        except RedisError as e:
            current_app.logger.error(e)
            total_num = 0
            res = []
        if total_num:#缓存存在
            return total_num,res
        else:#不存在
            try:
                rets = Article.query.options(load_only(Article.id,Article.ctime)).filter(Article.channel_id==self.channel_id,Article.status==Article.STATUS.DRAFT).all()
            except DatabaseError as e:
                current_app.logger.error(e)
                raise e
            artiles = []
            caches = []
            for ret in rets:#构造缓存数据结构
                artiles.append(ret.id)
                caches.append(ret.ctime.timestamp())
                caches.append(ret.id)
            if caches:
                try:#存入缓存
                    pl = self.redis_conn.pipeline()
                    pl.zadd(self.key,*caches)
                    pl.expire(self.key, constants.ChannelArticleCacheTTL.get_val())
                    results = pl.execute()#[20, True]
                    if results[0] and not results[1]:
                        self.redis_conn.delete(self.key)
                except RedisError as e:
                    current_app.logger.error(e)
            total_num = len(artiles)
            page_articles = artiles[(page-1)*page_num:page*page_num]#[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            return total_num,page_articles

class ArticlesDetailCache():
    '''
    string:   key:value
    :return:
    '''
    article_detail = {
        'title': fields.String(attribute='title'),
        'author_id': fields.Integer(attribute='user_id'),
        'pub_date': fields.DateTime(attribute='ctime', dt_format='iso8601'),
        'article': fields.Integer(attribute='article_id'),
        'content': fields.Integer(attribute='content'),
        'channel_id': fields.Integer(attribute='channel_id'),
    }
    def __init__(self,article_id):
        self.key = "article:content:{}".format(article_id)
        self.article_id = article_id
        self.redis_conn = current_app.redis_cluster
    def save(self):
        '''
        保存到缓存
        :return:
        '''
        #从数据库中获取
        try:#获取文章内容，及文章其他相关数据
            detail = Article.query.join(Article.content).options(load_only(Article.title,Article.user_id,Article.ctime,Article.id,Article.channel_id,Article.allow_comment),contains_eager(Article.content).load_only(ArticleContent.content)).filter(Article.id==self.article_id,Article.status==Article.STATUS.DRAFT).first()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        #构造文章数据结构
        detail_dict = {
            'title':detail.title,
            'user_id':str(detail.user_id),
            'create_time':str(detail.ctime)[:str(detail.ctime).find(' ')],
            'art_id':detail.id,
            'channel_id':detail.channel_id,
            'content':detail.content.content,
            'allow_comment':detail.allow_comment
        }
        # 获取文章作者相关信息
        user = user_cache.UserProfileCache(detail_dict.get('user_id')).get()
        detail_dict['user_name'] = user.get('user_name')
        detail_dict['head_photo'] = user.get('head_photo')
        detail_dict['career'] = user.get('career')
        detail_dict['code_year'] = user.get('code_year')
        # 缓存
        article_cache = json.dumps(detail_dict)
        try:
            self.redis_conn.setex(self.key, constants.ArticleDetailCacheTTL.get_val(), article_cache)
        except RedisError as e:
            current_app.logger.error(e)

        #响应数据
        return detail_dict
    def get(self):
        '''
        获取文章详情
        :return:
        '''
        #首先从redis中获取
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None

        if res:
            if res == b'-1':
                return None
            else:
                detail_dict = json.loads(res)
        else:
            detail_dict = self.save()
        detail_dict = self.addFields(detail_dict)
        return detail_dict
    def addFields(self,detail_dict):
        '''
        增加字段
        :param article_dict:
        :return:
        '''
        detail_dict['read_num'] = article_statistics.ArticleReadCount.get(self.article_id)
        detail_dict['comment_num'] = article_statistics.ArticleCommentCount.get(self.article_id)
        detail_dict['like_num'] = article_statistics.ArticleLikeCount.get(self.article_id)
        detail_dict['collection_num'] = article_statistics.ArticleCollectionCount.get(self.article_id)
        return detail_dict
    def clear(self):
        '''
        清楚缓存
        :return:
        '''
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)
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
    def is_allow_comment(self):
        '''
        判断是否允许评论
        :return:
        '''
        articles = self.get()
        if articles:
            res = articles
        else:
            res = self.save()
        return res.get("allow_comment")


class ArticleLikeCache():
    '''
    当前文章的点赞缓存
    '''
    def __init__(self,user_id,aid):
        self.key = "user:{}:article:{}:like".format(user_id,aid)
        self.user_id = user_id
        self.aid = aid
        self.redis_conn = current_app.redis_cluster
    def get(self):
        '''
        获取文章点赞缓存
        :return:
        '''
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res :
            return int(res)
        try:
            res = Attitude.query.options(load_only(Attitude.attitude)).filter(Attitude.user_id==self.user_id,Attitude.article_id==self.aid).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        attitude = res.attitude if res and res.attitude else -1
        try:
            self.redis_conn.setex(self.key, constants.ArticleUserNoAttitudeCacheTTL.get_val(), int(attitude))
        except RedisError as e:
            current_app.logger.error(e)

        return attitude

    def clear(self):
        """
        清除
        :return:
        """
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class ArticleAttitudeCache():
    '''
    当前文章的点赞缓存
    '''
    def __init__(self,aid):
        self.key = "article:{}:like".format(aid)
        self.aid = aid
        self.redis_conn = current_app.redis_cluster
    def get(self):
        '''
        获取文章点赞缓存
        :return:
        '''
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res :
            return json.loads(res)
        try:
            res = Attitude.query.options(load_only(Attitude.user_id)).filter(Attitude.article_id==self.aid,Attitude.attitude==Attitude.ATTITUDE.LIKING).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        user_ids = []
        for attitude in res:
            print("----------------->>",attitude.user_id)
            user_ids.append(attitude.user_id)
        print("================>",user_ids)
        try:
            self.redis_conn.setex(self.key, constants.ArticleUserNoAttitudeCacheTTL.get_val(), json.dumps(user_ids))
        except RedisError as e:
            current_app.logger.error(e)

        return user_ids

    def clear(self):
        """
        清除
        :return:
        """
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class CommentAttitudeCache():
    '''
    评论点赞
    '''
    def __init__(self,comment_id):
        self.key = "comment:{}:user_id"
        self.comment_id = comment_id
        self.redis_conn = current_app.redis_master
    def get(self):
        '''
        获取
        :return:
        '''
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res:
            return json.loads(res)
        try:
            cls = CommentLiking.query.options(load_only(CommentLiking.user_id)).filter(CommentLiking.comment_id==self.comment_id,CommentLiking.is_deleted==False).all()
        except Exception as e:
            current_app.logger.error(e)
            cls = None
        if not cls:
            return []
        commentLikes = []
        for cl in cls:
            commentLikes.append(cl.user_id)
        try:
            self.redis_conn.setex(self.key,constants.CommentsLikingCacheTTL.get_val(),json.dumps(commentLikes))
        except RedisError as e:
            current_app.logger.error(e)
        return commentLikes
    def exist(self,user_id):
        self.clear()
        uids = self.get()
        return user_id in uids
    def clear(self):
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)





