import json

from flask import current_app
from redis import RedisError
from sqlalchemy.orm import load_only

from caches import users,articles,statistics
from models.news import Comment
from caches import statistics
from . import constants

class CommentCache():
    '''
    评论信息
    '''
    def __init__(self,comment_id):
        self.key = "comment:{}".format(comment_id)
        self.comment_id = comment_id
        self.redis_conn = current_app.redis_cluster
    def get(self):
        #从缓存中获取数据
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res is None:
            return None
        else:
            comment = json.loads(res)
            comment = CommentCache.add_fields(comment)
            return comment
    @classmethod
    def add_fields(cls,comment_dict):
        '''
        添加其他字段
        :param comment_dict: 评论字典
        :return:
        '''
        user_data = users.UserProfileCache(comment_dict.get('author_id')).get()
        comment_dict['user_name'] = user_data.get("user_name")
        comment_dict['code_year'] = user_data.get('code_year')
        comment_dict['head_photo'] = user_data.get('head_photo')
        comment_dict['like_num'] = statistics.ArticleCommentLikeCount.get(comment_dict.get('comment_id'))
        comment_dict['comment_response_num'] = statistics.ArticleCommentResponseCount.get(comment_dict.get('comment_id'))
        return comment_dict
    def save(self,comment=None):
        '''
        缓存文章评论
        :param comment:
        :return:
        '''
        if comment is None:#保存缓存
            comment = Comment.query.filter(Comment.id==self.comment_id,Comment.status==Comment.STATUS.APPROVED).all()
        if comment is None:#数据库不存在返回NOne
            return None
        else:#数据库存在，存入缓存中
            comment_dict = {
                "comment_id":comment.id,
                "ctime":comment.ctime,
                "author_id":comment.user_id,
                "is_top":comment.is_top,
                "content":comment.content
            }
            try:
                self.redis_conn.setex(self.key,constants.CommentCacheTTL.get_val(),json.dumps(comment_dict))
            except RedisError as e:
                current_app.logger.error(e)
            return comment_dict
    def exist(self,comment_id):
        '''
        判断缓存是否存在
        :param comment_id:
        :return:
        '''
        res = self.get()
        if res:
            return False if res == b'-1'  else True
        else:
            ret = self.save()
            if ret is None:
                self.redis_conn.setex(self.key,constants.CommentNotExistsCacheTTL.get_val(),-1)
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
    @classmethod
    def get_list(cls,comment_id):
        '''
        获取指定评论信息
        :param comment_id:
        :return:
        '''
        query = []
        return_data = []
        comments_dict = {}
        for cid in comment_id:
            comment = CommentCache(cid).get()
            if comment:#存在，加入返回数据列表
                comments_dict[cid] = comment
                return_data.append(comment)
            if not comment:
                query.append(cid)
        if not query:#不需要查查询数据库，直接返回
            return return_data
        else:
            res = Comment.query.filter(Comment.id in query,Comment.status==Comment.STATUS.APPROVED).all()
            pl = current_app.redis_cluster.pipeline()
            for comment in res:
                comment_dict = {
                    "comment_id": comment.id,
                    "ctime": comment.ctime,
                    "author_id": comment.user_id,
                    "is_top": comment.is_top,
                    "content": comment.content
                }
                pl.setex(CommentCache(comment.id).key,constants.CommentCacheTTL.get_val(),json.dumps(comment_dict))
                comment_dict = cls.add_fields(comment_dict)
                comments_dict[comment_dict.id] = comment_dict
            try:
                pl.execute()
            except RedisError as e:
                current_app.logger.error(e)
            return_data = []
            for cid in comment_id:
                return_data.append(comments_dict.get(cid))
            return return_data

class ArticleCommentBaseCache():
    '''
    某篇文章评论父类
    '''
    def __init__(self,id_value):
        self.id_value = id_value
        self.key = self._set_key
        self.redis_conn = current_app.redis_cluster

    def _set_key(self):
        """
        设置缓存键
        """
        return ''

    def _get_total_count(self):
        """
        获取总量
        :return:
        """
        return 0

    def _db_query_filter(self, query):
        """
        数据库查询条件
        :return:
        """
        return query

    def _get_cache_ttl(self):
        """
        获取缓存有效期
        :return:
        """
        return 0
    def get_page(self,offset,limit):
        '''
        分页获取
        :param offset: 偏移量
        :param limit: 限制几条
        :return:评论 id
        '''
        try:
            pl = self.redis_conn.pipeline()
            pl.zcard(self.key)#返回有序集 key 的基数
            pl.zrange(self.key,0,0,withscores=True)#返回有序集 key 中，指定区间内的成员。
            # withscores 选项，来让成员和它的 score 值一并返回，返回列表以      value1,score1, ..., valueN,scoreN      的格式表示
            if offset is None:#从头到尾 返回有序集 key 中，指定区间内的成员
                pl.zrevrange(self.key,0,limit-1,withscores=True)# ZREVRANGE key start stop [WITHSCORES]
            else:# ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]
                pl.zrevrangebyscore(self.key,offset-1,0,0,limit-1,withscores=True)
            total_num,end_id,res = pl.execute()
        except Exception as e:
            current_app.logger.error()
            total_num = 0
            end_id = None
            last_id = None
            res = []
        if total_num > 0:#缓存存在
            end_id = int(end_id[0][1])
            # ret -> [(value, score)...] [(comment_id,score)]
            last_id = int(res[-1][1]) if res else None
            return total_num, end_id, last_id, [int(cid[0]) for cid in res]
        #缓存不存在
        total_num = self._get_total_count()#判断是否有评论
        if total_num  == 0:
            return 0,None,None,[]
        #只加载指定数据
        query = Comment.query.options(load_only(Comment.id, Comment.ctime, Comment.is_top))
        #过滤
        query = self._db_query_filter(query)
        #按指定降序排序
        ret = query.order_by(Comment.is_top.desc(), Comment.id.desc()).all()

        cache = []
        page_comments = []
        page_count = 0
        total_count = len(ret)
        page_last_comment = None

        for comment in ret:
            score = comment.ctime.timestamp()
            if comment.is_top:
                score += constants.COMMENTS_CACHE_MAX_SCORE

            # 构造返回数据
            if ((offset is not None and score < offset) or offset is None) and page_count <= limit:
                page_comments.append(comment.id)
                page_count += 1
                page_last_comment = comment

            # 构造缓存数据
            cache.append(score)
            cache.append(comment.id)

        end_id = ret[-1].ctime.timestamp()
        last_id = page_last_comment.ctime.timestamp() if page_last_comment else None

        # 设置缓存
        if cache :
            try :
                pl = self.redis_conn.pipeline()
                pl.zadd(self.key, *cache)
                pl.expire(self.key, self._get_cache_ttl())
                results = pl.execute()
                if results[0] and not results[1] :
                    self.redis_conn.delete(self.key)
            except RedisError as e :
                current_app.logger.error(e)
        return total_count , end_id , last_id , page_comments
    def add(self,comment) :
        '''
        添加评论
        :return:
        '''
        try :
            ttl = self.redis_conn.ttl(self.key)
            if ttl > constants.ALLOW_UPDATE_ARTICLE_COMMENTS_CACHE_TTL_LIMIT:
                score = comment.ctime.timestamp()
                self.redis_conn.zadd(self.key,score,comment.id)
        except RedisError as e:
            current_app.logger.error(e)
    def clear(self):
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class ArticleCommentCache(ArticleCommentBaseCache):
    '''
    文章评论
    '''

    def _set_key(self):
        """
        设置缓存键
        """
        return "article:comment:{}".format(self.id_value)

    def _get_total_count(self):
        """
        获取总量
        :return:
        """
        count = statistics.ArticleCommentCount.get(self.id_value)
        return count

    def _db_query_filter(self, query):
        """
        数据库查询条件
        :return:
        """
        return query.filter(Comment.article_id==self.id_value,Comment.status==Comment.STATUS.APPROVED,Comment.parent_id==None)

    def _get_cache_ttl(self):
        """
        获取缓存有效期
        :return:
        """
        return constants.ArticleCommentsCacheTTL.get_val()

class ArticleCommentResponseCache(ArticleCommentBaseCache):
    '''
    文章评论
    '''

    def _set_key(self):
        """
        设置缓存键
        """
        return "article:comment:response:{}".format(self.id_value)

    def _get_total_count(self):
        """
        获取总量
        :return:
        """
        count = statistics.ArticleCommentResponseCount.get(self.id_value)
        return count

    def _db_query_filter(self, query):
        """
        数据库查询条件
        :return:
        """
        return query.filter(Comment.article_id==self.id_value,Comment.status==Comment.STATUS.APPROVED)

    def _get_cache_ttl(self):
        """
        获取缓存有效期
        :return:
        """
        return constants.CommentRepliesCacheTTL.get_val()