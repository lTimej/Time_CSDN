from fdfs_client.client import Fdfs_client
# #
client = Fdfs_client('/home/time/Time_CSDN/Time_CSDN/common/utils/fdfs/client.conf')
ret = client.upload_by_filename('./t3.png')
print(ret)

