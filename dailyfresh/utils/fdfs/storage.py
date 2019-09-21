from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client, get_tracker_conf
from django.conf import settings


class FDFSStorage(Storage):
    """
    自定义FastDFS文件存储类,需要实现一些默认上传类的方法
    因为默认上传类FileSystemStorage中有_open和_save方法
    且django在上传的时候会调用这些方法所以自定义类也必须有这些方法
    需要修改 DEFAULT_FILE_STORAGE = 'utils.fdfs.storage.FDFSStorage'
    才能使用这个类上传
    """

    def __init__(self, client_conf=None, base_url=None):
        """让这个类可以更方便的修改参数"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        """打开文件时使用,即使不用也要定义这个方法"""
        pass

    def _save(self, name, content):
        """保存文件时使用"""
        # name: 上传文件的名字
        # content: 包含上传文件的File对象

        # 创建一个fdfs_client对象
        # fdfs_client接收的是tracker对象,而不是一个字符串
        tracker = get_tracker_conf(self.client_conf)
        client = Fdfs_client(tracker)
        # 上传文件到fdfs系统中,返回值是一个包含上传结果的字典
        res = client.upload_by_buffer(content.read())

        # return dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }

        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('文件上传至fdfs系统失败')
        # 获取返回的文件ID
        filename = res.get('Remote file_id')
        # 返回文件名
        # print(type(filename))
        # 这里需要返回的是str类型,而不是bytes类型
        return filename.decode('utf-8')

    def exists(self, name):
        """django判断文件名是否可用,即使不用也要定义这个属性"""
        return False

    def url(self, name):
        """返回访问文件的url路径"""
        return self.base_url + name
