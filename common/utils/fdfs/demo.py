# from fdfs_client.client import Fdfs_client
# # #
# client = Fdfs_client('/home/time/Time_CSDN/Time_CSDN/common/utils/fdfs/client.conf')
# ret = client.upload_by_filename('./t3.png')
# print(ret)

d = {"id":1,"channel_name":"python"}
c = {"id":1,"channel_name":"python"}
a = [
    {"id":1,"channel_name":"python"},
    {"id":2,"channel_name":"python1"},
    {"id":3,"channel_name":"python2"},
    {"id":4,"channel_name":"python3"},
    {"id":5,"channel_name":"python4"},
    {"id":6,"channel_name":"python5"},
]
b = [
    {"id":1,"channel_name":"python"},
    {"id":3,"channel_name":"python2"},
    {"id":4,"channel_name":"python3"},
    {"id":5,"channel_name":"python4"},
]
for i in a:
    if i not in b:
        print(i)
