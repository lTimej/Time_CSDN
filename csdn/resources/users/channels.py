import json

from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser

from flask import g,current_app
from redis.exceptions import RedisError

from caches import constants
from caches.channels import AnonyUserChannel,UserArticleChannel
from models import db
from utils import parsers
from utils.decorator import is_login

from models.news import UserChannel,Channel


class UserChannelView(Resource):
    method_decorators = [is_login]
    def _save(self,channel):
        '''
        保存数据库
        :return:
        '''
        try:
            #修改
            uc = UserChannel.query.filter_by(user_id=g.user_id, channel_id=channel.get('id'),is_deleted=1).first()
            if uc:
                uc.is_deleted = False
                db.session.add(uc)
                db.session.commit()
            else:#保存
                user_channel = UserChannel(user_id=g.user_id, channel_id=channel.get('id'))
                # 保存数据库
                db.session.add(user_channel)
                db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return {'message': "data Invalid"}, 401
    def get(self):
        '''
        匿名用户频道
        :return:
        '''
        #匿名用户
        channels = AnonyUserChannel.get()
        user_channels = []
        if g.user_id:#登录用户
            #获取频道缓存
            user_channels = UserArticleChannel(g.user_id).get()
            # 如果为空，这季节把匿名用户关注频道保存数据库，并返回
            if not user_channels:
                #保存数据库
                if not channels:
                    return {'channels': channels}, 201
                for channel in channels:
                    self._save(channel)
                # 更新数据库，就要更新缓存
                UserArticleChannel(g.user_id).clear()
                return {'channels': channels}, 201
            #如果不为空
            n = len(user_channels)
            #数据库有，做去重处理

            #判断匿名用户缓存是否有
            if not channels:#没有直接返回登录用户的数据
                # 存匿名用户缓存中
                AnonyUserChannel.save(user_channels)
                return {'channels': user_channels}, 201
            for channel in channels:
                #查看是否存在
                flag = UserArticleChannel(g.user_id).exist(channel.get('id'))
                #如果不存在
                if not flag:
                    print(111111111111111)
                    #保存数据库
                    self._save(channel)
                    user_channels.append(channel)
                    # 更新数据库，就要更新缓存
                    UserArticleChannel(g.user_id).clear()
            channels = user_channels
        return {'channels': channels}, 201
    def post(self):
        '''
        添加频道
        :return:
        '''
        data = RequestParser()
        data.add_argument('channel_id',type=inputs.positive,required=True,location='json')
        data.add_argument('channel_name',type=parsers.checkout_channel_name,required=True,location='json')
        args = data.parse_args()

        channel_id = args.channel_id
        channel_name = args.channel_name
        channels_dict = {
            "id": channel_id,
            "channel_name": channel_name
        }
        #获取匿名用户缓存频道
        if not g.user_id:
            flag = AnonyUserChannel.exist(channel_id)
            if not flag:
                #获取原有匿名用户频道缓存
                channels = AnonyUserChannel.get()
                #将新的添加到列表
                if not channels:
                    channels = []
                channels.append(channels_dict)
                #重新做缓存
                AnonyUserChannel.save(channels)
                return {"channels":channels},201
            else:
                return {"message": "It is exist"}, 400
        else:#已登录用户
            flag = UserArticleChannel(g.user_id).exist(channel_id)
            if not flag:
                self._save(channels_dict)
                # 更新数据库，就要更新缓存
                UserArticleChannel(g.user_id).clear()

                channels = UserArticleChannel(g.user_id).get()
                #存匿名用户缓存中
                AnonyUserChannel.save(channels)
                return {'channels': channels}, 201
            else:
                return {"message":"It is exist"},400
    def patch(self):
        '''
        将is_deleted改为true
        :return:
        '''
        data = RequestParser()
        data.add_argument('channel_id', type=inputs.positive, required=True, location='json')
        args = data.parse_args()
        channel_id = args.channel_id
        # 获取匿名用户缓存频道
        if not g.user_id:
            flag = AnonyUserChannel.exist(channel_id)
            if not flag:
                return {"message": "It is not exist"}, 400
            else:
                # 获取原有匿名用户频道缓存
                channels = AnonyUserChannel.get()
                # 删除对应的频道
                for channel in channels:
                    if channel.get('id') == channel_id:
                        channels.remove(channel)
                        break
                # 重新做缓存
                AnonyUserChannel.save(channels)
                return {"channels": channels}, 201
        else:  # 已登录用户
            flag = UserArticleChannel(g.user_id).exist(channel_id)
            if not flag:
                return {"message": "It is not exist"}, 400
            else:
                UserChannel.query.filter_by(user_id=g.user_id, channel_id=channel_id).update({'is_deleted':True})
                db.session.commit()
                # 更新数据库，就要更新缓存
                UserArticleChannel(g.user_id).clear()
                channels = UserArticleChannel(g.user_id).get()
                # 存匿名用户缓存中
                AnonyUserChannel.save(channels)
                return {'channels': channels}, 201




