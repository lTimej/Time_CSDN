from fdfs_client.client import Fdfs_client

client = Fdfs_client('./client.conf')

ret = client.upload_by_filename('./t3.png')
print(ret)