from flask import current_app


def upload_photo(file_data):
    '''
    上传图片
    :param file_data: 文件名
    :return:

    {'Group name': 'group1',
    'Remote file_id': 'group1/M00/00/00/wKiZgmCOpa6AbvCXAAEwN58xN6E181.png',
    'Status': 'Upload successed.', 'Local file name': './t3.png',
    'Uploaded size': '76.00KB', 'Storage IP': '192.168.153.130'}
    '''
    #上传
    res = current_app.fdfs_client.upload_by_filename(file_data)
    if res.get('Status') == 'Upload successed.':#成功，返回文件储存名
        return res.get('Remote file_id')
    else:#不成功返回None
        return None