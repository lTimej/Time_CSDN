from server import sio,JWT_SECRET
from utils.getJwt import verify_token
from werkzeug.wrappers import Request

def JWT_verify(token):
    '''
    token验证
    :param token:
    :return:
    '''
    payload = verify_token(token,JWT_SECRET)
    if payload is None:
        return None
    else:
        return payload.get('user_id')

@sio.on('connect')
def on_connect(sid,environ):
    '''
    建立起与客户端的连接
    :param sid:
    :param environ:
    :return:
    '''
    request = Request(environ)
    token = request.args.get("token")

    user_id = JWT_verify(token)
    print("-----===========/////",user_id)
    if user_id:
        sio.enter_room(sid,room=user_id)

@sio.on('disconnect')
def on_disconnect(sid):
    rooms = sio.rooms(sid)
    for room in rooms:
        sio.leave_room(sid,room)



