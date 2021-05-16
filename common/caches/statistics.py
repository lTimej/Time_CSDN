from flask import current_app

from redis.exceptions import RedisError
from sqlalchemy import func

from models.user import Relation,Visitors
from models.news import Article,ArticleStatistic,Comment,Collection,CommentLiking,Attitude
from models import db

class CountStorageBase(object):
    '''
    所有用户相关数量统计父类
    redis cluster 不支持多键操作，采用sentinel
    redis存储类型 zset
    key :        vlaue :  scrore
    哪种数量统计  用户id    count
      1、增加  incr
      2、获取   get
      3、重置  reset
    '''
    key = ""#不同用户不同key

    @classmethod
    def get(cls,user_id):
        '''
        获取用相关数量
        :param user_id: 用户id
        :return:
        '''
        try:#先从主获取
            count = current_app.redis_master.zscore(cls.key,user_id)
        except RedisError as e:#主挂了，从获取
            current_app.logger.error(e)
            count = current_app.redis_slave.zscore(cls.key,user_id)
        if not count:#没有返回0
            return 0
        else:
            return int(count)
    @classmethod
    def incr(cls,user_id,incr_num):
        '''
        数量自增     eg:用户点击关注，则关注量自增1
        :param user_id:
        :return:
        '''
        try:
            current_app.redis_master.zincrby(cls.key,user_id,incr_num)
        except RedisError as e:
            current_app.logger.error(e)
            raise e#增加出错，主动抛出异常给调用者

    @classmethod
    def reset(cls,user_id,db_query_res):
        '''
        重新刷新缓存，一般每天凌晨3点旧更新一次缓存

        :param user_id: 用户id
        :param db_query: 要重新存入的数据
        :return:
        '''
        #初始化一个列表，存入用户id和count,号直接解包存入zset中
        counts = []
        for user_id,count in db_query_res:
            counts.append(count)
            counts.append(user_id)
        #管道对象
        pl = current_app.redis_master.pipeline()
        # pl.zadd(cls.key, count1, user_id1, count2, user_id2, ..]
        pl.zadd(cls.key,*counts)
        pl.execute()

class UserArticleCount(CountStorageBase):
    '''
            用户关注数
    关注表 Relation:
    一个用户可以右多个关注对象，采用分组聚合查询
    '''
    key = "user:article:count"
    #直接类名调用
    @staticmethod
    def db_query():
        '''
        返回所有用户的关注数量
        user_id:count
        :return:
        '''
        #查询每个用户关注的人数，过滤出是关注模式，通过用户id来分组
        return db.session.query(Article.user_id, func.count(Article.id)) \
            .filter(Article.status == Article.STATUS.APPROVED) \
            .group_by(Article.user_id).all()
class UserFocusCount(CountStorageBase):
    '''
            用户关注数
    关注表 Relation:
    一个用户可以右多个关注对象，采用分组聚合查询
    '''
    key = "user:focus:count"
    #直接类名调用
    @staticmethod
    def db_query():
        '''
        返回所有用户的关注数量
        user_id:count
        :return:
        '''
        #查询每个用户关注的人数，过滤出是关注模式，通过用户id来分组
        return db.sessiom.query(Relation.user_id,func.count(Relation.target_user_id)).filter(Relation.relation==Relation.RELATION.FOLLOW).group_by(Relation.user_id).all()

class UserFansCount(CountStorageBase):
    '''
    用户粉丝数量
    关注表 ：  一个用户可以右多个关注对象，也可以关注多个人
    '''
    key = "user:fans:count"

    @staticmethod
    def db_query():
        '''
        返回所有用户的粉丝数量
        user_id:count
        :return:
        '''
        return db.session.query(Relation.target_user_id,func.count(Relation.user_id)).filter(Relation.relation==Relation.RELATION.FOLLOW).group_by(Relation.target_user_id).all()

class UserVisitCount(CountStorageBase):
    '''
    用户被访问数量

    '''
    key = "user:visit:count"

    @staticmethod
    def db_query():
        '''
        返回所有用户被访问的数量
        user_id : visits
        :return:
        '''
        return db.session.query(Visitors.count).all()

class ArticleReadCount(CountStorageBase):
    '''
    某篇文章访问量
    '''
    key = "article:read:count"

class UserArticleReadCount(CountStorageBase):
    '''
    用户所有阅读量
    '''
    key = "user:article:read:count"

class ArticleCommentCount(CountStorageBase):
    '''
    文章评论数
    '''
    key = "article:comment:count"
    @staticmethod
    def db_query():
        return db.session.query(Comment.article_id,func.count(Comment.id)).filter(Comment.status==Comment.STATUS.APPROVED).group_by(Comment.article_id).all()

class ArticleCommentResponseCount(CountStorageBase):
    '''
    文章评论回复
    '''
    key = "article:comment:response:count"
    @staticmethod
    def db_query():
        return db.session.query(Comment.parent_id,func.count(Comment.id)).filter(Comment.status==Comment.STATUS.APPROVED,Comment.parent_id!=None).group_by(Comment.parent_id).all()

class ArticleCommentResponseLikeCount(CountStorageBase):
    '''
    文章评论点赞数
    '''
    key = "article:comment:like:count"
    @staticmethod
    def db_query():
        return db.session.query(CommentLiking.comment_id,func.count(CommentLiking.comment_id)).filter(CommentLiking.is_deleted==0).group_by(CommentLiking.comment_id).all()

class ArticleLikeCount(CountStorageBase):
    '''
    文章点赞数
    '''
    key = "article:like:count"
    @staticmethod
    def db_query():
        return db.session.query(Attitude.article_id,func.count(Attitude.article_id)).filter(Attitude.attitude==Attitude.ATTITUDE.LIKING).group_by(Attitude.article_id).all()

class ArticleCollectionCount(CountStorageBase):
    '''
    文章收藏量
    '''
    key = "article:collection:count"
    @staticmethod
    def db_query():
        return db.session.query(Collection.article_id,func.count(Collection.article_id)).filter(Collection.is_deleted==0).group_by(Collection.article_id).all()
