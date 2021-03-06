from flask_restful import Resource
from flask_restful.inputs import positive, int_range
from flask_restful.reqparse import RequestParser
from flask import current_app,g
from sqlalchemy.exc import SQLAlchemyError

from models import db
from models.news import Comment
from utils import parsers
from utils.decorator import login_required
from utils.snowflake import id_worker
from . import constants
from caches import comments, articles,statistics


class CommentView(Resource):
    '''
    评论
    '''
    method_decorators = {
        'post': [login_required],
    }
    def _comment_type(self,value):
        '''
        评论类型验证
        :param value:
        :return:
        '''
        if value in ['a','c']:
            return value
        else:
            return ValueError("type is failed")
    def get(self):
        '''
        :return:
        '''
        user_id = g.user_id
        print("[======user_id==========]",user_id)
        data = RequestParser()
        data.add_argument('type', type=self._comment_type, required=True, location='args')
        #offset为时间戳
        data.add_argument('article_id', type=parsers.checkout_int, required=True, location='args')
        data.add_argument('offset', type=positive, required=False, location='args')
        data.add_argument('limit', type=int_range(constants.DEFAULT_COMMENT_PER_PAGE_MIN,
                                                       constants.DEFAULT_COMMENT_PER_PAGE_MAX,
                                                       argument='limit'), required=False, location='args')
        args = data.parse_args()
        #文章评论条数
        limit = args.limit if args.limit is not None else constants.DEFAULT_COMMENT_PER_PAGE_MIN
        #当前文章id
        article_id = args.article_id

        #获取文章评论缓存id
        total_num , end_id , last_id , page_comments = comments.ArticleCommentCache(article_id).get_page(args.offset,limit)
        comment_list = comments.CommentCache.get_list(page_comments)
        for comment in comment_list:
            flag = articles.CommentAttitudeCache(int(comment.get('comment_id'))).exist(user_id)
            comment['comment_is_like'] = flag
            total_num, end_id, last_id, page_comments = comments.ArticleCommentResponseCache(int(comment.get('comment_id'))).get_page(
                args.offset, limit)
            comments_list = comments.CommentCache.get_list(page_comments)

            if not page_comments:
                comment['cComments'] = []
                continue
            for c in comments_list:
                if int(c.get('parent_comment_id')) == int(comment.get('comment_id')):
                    flag = articles.CommentAttitudeCache(int(c.get('comment_id'))).exist(user_id)
                    print("-------flag----",flag)
                    c['comment_is_like'] = flag
                    comment['cComments'] = comments_list
        total_num = statistics.ArticleCommentCount.get(article_id)
        return {"total_num":total_num,"end_id":end_id,'last_id':last_id,'comments':comment_list},201

    def post(self):
        '''
        评论
        :return:
        '''
        #获取当前用户
        user_id = g.user_id
        #获取参数
        data = RequestParser()
        #校验参数
        data.add_argument('article_id',type=parsers.checkout_article_id,required=True,location='json')
        data.add_argument('content', required=True, location='json')
        data.add_argument('comment_id',type=positive,required=False,location='json')
        args = data.parse_args()
        #解析参数
        article_id = args.article_id
        content = args.content
        comment_parent_id = args.comment_id
        if not content:#评论内容不为空
            return {'message': 'Empty content.'}, 400
        #判断该文章是否可以评论
        allow_comment = articles.ArticlesDetailCache(article_id).is_allow_comment()
        if not allow_comment:
            return {'message': 'Article denied comment.'}, 400
        if not comment_parent_id:#评论当前文章
            # 判断是否评论过
            f = comments.ArticleCommentCache(article_id).exist()
            if f:#如果评论过，不能再次评论
                return {"message": "comment is exist"}, 400
            #获取独一无二的评论id
            comment_id = current_app.id_worker.get_id()
            try:
                comment = Comment(id=comment_id,user_id=user_id,article_id=article_id,content=content,parent_id=None)
                db.session.add(comment)
                db.session.commit()
            except SQLAlchemyError as e:
                current_app.logger.error(e)
                db.session.rollback()
                return {"message":"data is invalid"},401
            #文章评论自增1
            statistics.ArticleCommentCount.incr(article_id, 1)
            try:#保存评论内容缓存中
                comments.CommentCache(comment_id).save(comment)
            except SQLAlchemyError as e:
                current_app.logger.error(e)
            #保存评论id缓存
            comments.ArticleCommentCache(article_id).add(comment)
        else:#评论当前文章的评论
            #判断是否评论过
            f = comments.ArticleCommentResponseCache(comment_parent_id).exist()
            if f:#如果评论过，不能再次评论
                return {"message": "comment is exist"}, 401
            # 判断当前文章的评论在不在
            flag = comments.CommentCache(comment_parent_id).exist()
            if not flag:
                return {'message': 'Invalid target comment id.'}, 400
            # 获取独一无二的评论id
            comment_id = current_app.id_worker.get_id()
            #保存数据库
            try:
                comment = Comment(id=comment_id, user_id=user_id, article_id=article_id, content=content, parent_id=comment_parent_id)
                db.session.add(comment)
                db.session.commit()
            except SQLAlchemyError as e:
                current_app.logger.error(e)
                db.session.rollback()
                return {"message":"data is invalid"},401
            #子评论数目自增1
            statistics.ArticleCommentResponseCount.incr(comment_parent_id, 1)
            #文章评论数自增1
            statistics.ArticleCommentCount.incr(article_id,1)
            try:#保存子评论评论内容
                comments.CommentCache(comment_id).save(comment)
            except SQLAlchemyError as e:
                current_app.logger.error(e)
            comments.ArticleCommentResponseCache(comment_parent_id).add(comment)
        return {'comment_id': comment.id, 'art_id': article_id,'parent_comment_id':comment_parent_id}, 201


