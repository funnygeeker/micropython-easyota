# https://github.com/funnygeeker/micropython-easyota
# GPL3.0
# 参考资料：
# https://blog.csdn.net/jd3096/article/details/126594241
# senko

from libs import urequests
import binascii
import hashlib
import time
import os


def os_pathtype(path: str):
    """判断路径类型"""
    try:
        result = os.stat(path)  # 获取路径的信息
        if result[0] & 0o170000 == 0o040000:  # 检查文件类型
            return 'dir'  # 如果是目录
        else:
            return 'file'  # 如果是文件
    except OSError:  # 路径不存在或无法访问
        return None  # 返回 None


def os_makedirs(path):
    """逐级创建目录"""
    # 分割路径为目录名列表
    folders = path.strip('/').split('/')
    # 逐级创建目录
    for i in range(len(folders)):
        folder = '/'.join(folders[:i + 1])
        if not os_exists(folder):
            os.mkdir(folder)


def os_movefiles(old, new):
    """移动目录下的文件到另一个目录"""
    old = old.rstrip("/")
    new = new.rstrip("/")
    dirs = os.listdir(old)
    for d in dirs:
        os.rename("{}/{}".format(old, d), "{}/{}".format(new, d))


def os_removedirs(path):
    """逐级删除目录"""
    for file in os.listdir(path):
        file_path = "{}/{}".format(path, file)
        if os.stat(file_path)[0] & 0o170000 == 0o40000:
            os_removedirs(file_path)  # 递归删除子目录
        else:
            os.remove(file_path)  # 删除文件
    os.rmdir(path)  # 删除目录本身


def os_isdir(path):
    """判断路径为文件夹"""
    return os_pathtype(path) == 'dir'


def os_isfile(path):
    """判断路径为文件"""
    return os_pathtype(path) == 'file'


def os_exists(path):
    """判断路径是否存在"""
    return os_pathtype(path) is not None


def hash_decode(sha1_hash):
    """Hash 解码"""
    return binascii.hexlify(sha1_hash).decode('utf-8')


class EasyOTA:
    GITHUB_API = 'https://api.github.com/repos/{user}/{repo}/git/trees/{branch}?recursive=1'
    GITHUB_RAW = 'https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}'
    GITEE_API = 'https://gitee.com/api/v5/repos/{user}/{repo}/git/trees/{branch}?recursive=1'
    GITEE_RAW = 'https://gitee.com/{user}/{repo}/raw/{branch}/{path}'

    def __init__(self, user: str, repo: str, branch: str,
                 files: list = None, ignore: list = None,
                 git_raw: str = None, git_api: str = None,
                 local_path: str = '', remote_path: str = '', cache_path: str = 'easyota_cache',
                 callback=None, headers: dict = None, check: bool = False):
        """
        Args:
            user: 用户
            repo:  仓库
            branch: 分支，一般为 `main` 或者 `master`
            files: 需要检查的文件和路径，以 local_path 为标准的相对目录（默认为检查全部）
            ignore: 不需要检查的文件，以 local_path 为标准的相对目录（默认为无）
            git_raw: Git 原始文件地址
            git_api: Git 文件树 API 地址
            local_path: 需要检查的本地目录
            remote_path: 需要检查的远程 (Git) 目录
            cache_path: 更新文件的缓存目录
            callback: 回调函数，用于返回检查状态和进度
            headers: urequests 请求头
            check: 启用二次校验，可最大程度避免文件不一致，但是需要花时间额外检查一次文件
        """
        self.files = files or []
        self.ignore = ignore or []
        self.git_raw = git_raw or EasyOTA.GITHUB_RAW
        self.git_api = git_api or EasyOTA.GITHUB_API
        self.local_path = local_path.strip('/')
        self.remote_path = remote_path.strip('/')
        self.cache_path = cache_path.strip('/')
        self.git_raw = self.git_raw.format(user=user, repo=repo, branch=branch, path=self.remote_path)
        self.git_api = self.git_api.format(user=user, repo=repo, branch=branch)
        self.callback = callback
        self.headers = headers or {'User-Agent':
                                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                       "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.49"
                                   }
        self.check = check
        self.changes = []
        self.last_time = None

    def _list_files(self, path: str, level: int = 100, _level: int = 1) -> tuple:
        """
        列出所有文件和目录（相对目录）

        Args:
            path: 起始目录
            level: 最大文件夹层数
            _level: 当前所在的文件夹层数（一般不需要修改）
        """
        files = []  # 文件列表
        dirs = []  # 目录列表
        local_path = "{}/".format(self.local_path)
        if not os_exists(path):
            print("[WARNING] Folder does not exists, creating folder...")
            os_makedirs(path)
        items = os.listdir(path)
        for item in items:
            _path = "{}/{}".format(path, item)
            if os_isdir(_path):
                dirs.append(_path.lstrip("{}/".format(self.local_path)))
                if _level <= level:  # 超过最大深度则不继续列出
                    files_list, dirs_list = self._list_files(_path, level, _level + 1)
                    files.extend(files_list)
                    dirs.extend(dirs_list)
            elif os_isfile(_path):
                files.append(_path.lstrip(local_path))  # 绝对路径转换为相对路径后添加到列表
        return files, dirs

    @staticmethod
    def _download_file(url: str, file: str, headers: dict):
        """
        获取文件

        Returns:
            True: 成功
            None: 失败
        """
        response = None
        try:
            response = urequests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                raise Exception("status code - {}".format(response.status_code))
            data = response.raw.read(10240)
            with open(file, "wb") as f:
                while data:
                    f.write(data)
                    data = response.raw.read(10240)
        except Exception as e:
            print("[ERROR] An error occurred while downloading the file: {}".format(e))
            return None
        finally:
            if response:
                response.close()
        return True

    @staticmethod
    def _local_hash(file: str):
        """
        校验本地文件哈希值

        Args:
            file: 文件路径

        Returns:
            哈希值
        """
        with open(file, "rb") as f:
            _hash = hashlib.sha1()
            data = f.read(10240)
            while data:
                _hash.update(data)
                data = f.read(10240)
        return hash_decode(_hash.digest())

    @staticmethod
    def _remote_hash(url: str, headers: dict):
        """
        校验服务器文件的哈希

        Args:
            url: 文件链接
            headers: requests 请求头

        Returns:
            hex 哈希结果
        """
        response = None
        try:
            response = urequests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                raise Exception("status code - {}".format(response.status_code))
            _hash = hashlib.sha1()
            data = response.raw.read(10240)
            while data:
                _hash.update(data)
                data = response.raw.read(10240)
        except Exception as e:
            print("[ERROR] Error occurred while fetching remote data: {}".format(e))
            return None
        finally:
            if response:
                response.close()
        return hash_decode(_hash.digest())

    def _check_all(self):
        """
        检查全部文件一致性
        """
        # 要忽略的目录和文件
        self._not_check_files = set()
        self._not_check_dirs = set()
        for _ in self.ignore:
            _ = _.strip("/")
            path = "{}/{}".format(self.local_path, _)
            if os_isfile(path):
                self._not_check_files.add(_)
            elif os_isdir(path):
                self._not_check_dirs.add(_)
            else:  # 路径不存在，则同时考虑两种情况
                self._not_check_files.add(_)
                self._not_check_dirs.add(_)
        # 本地已有且需要同步的目录和文件
        self._local_files = set()
        self._local_dirs = set()
        if self.files:
            for _ in self.files:
                _ = _.strip("/")
                if _:  # 过滤空的路径
                    path = "{}/{}".format(self.local_path, _).lstrip("/")
                    if os_isfile(path) and _ not in self._not_check_files:  # 文件不被忽略且不属于被忽略的文件夹内
                        for i in self._not_check_dirs:
                            if path.startswith(i):
                                break
                        else:
                            self._local_files.add(_)
                    elif os_isdir(path):
                        for i in self._not_check_dirs:  # 文件夹不被忽略且不属于被忽略的文件夹内
                            if path.startswith(i):
                                break
                        else:
                            self._local_dirs.add(_)
                    else:  # 路径不存在
                        pass
        else:
            files, dirs = self._list_files(self.local_path)  # 列出本地目录
            for _ in files:
                _ = _.strip("/")
                path = "{}/{}".format(self.local_path, _).lstrip("/")
                if os_isfile(path) and _ not in self._not_check_files:  # 文件不被忽略且不属于被忽略的文件夹内
                    for i in self._not_check_dirs:
                        if path.startswith(i):
                            break
                    else:
                        self._local_files.add(_)
            for _ in dirs:
                _ = _.strip("/")
                path = "{}/{}".format(self.local_path, _).lstrip("/")
                for i in self._not_check_dirs:  # 文件夹不被忽略且不属于被忽略的文件夹内
                    if path.startswith(i):
                        break
                else:
                    self._local_dirs.add(_)
        # print("get remote file list...\n{}".format(self.git_api))
        # Git 仓库已有且需要同步的目录和文件
        self._remote_files = set()
        self._remote_dirs = set()
        try:
            response = urequests.get(self.git_api, headers=self.headers)
        except:
            print("[ERROR] API request failed: Failed to connect to server.")
            return None
        if response.status_code == 200:
            for _ in response.json()['tree']:
                _["path"] = _["path"].strip("/").lstrip(self.remote_path)
                if _["path"].startswith(self.remote_path) and _["path"]:  # 筛选指定目录，过滤路径为空的情况
                    if _["type"] == "blob" and _["path"] not in self._not_check_files:  # 是文件且不属于被忽略的文件夹内
                        for i in self._not_check_dirs:
                            if _["path"].startswith(i):
                                break
                        else:
                            self._remote_files.add(_["path"])
                    elif _["type"] == "tree":  # 是文件夹且不被忽略
                        for i in self._not_check_dirs:
                            if _["path"].startswith(i):
                                break
                        else:
                            self._remote_dirs.add(_["path"])
                    else:  # 路径类型不支持
                        pass
        else:
            print("[ERROR] API request failed: status code - {}".format(response.status_code))
            return None  # 检查失败
        
        if self.files:  # 指定了需要更新的文件范围
            files_set = set(self.files)
            self._local_files &= files_set
            self._remote_files &= files_set
            self._remote_dirs &= files_set
            self._local_dirs &= files_set
        self.change_files = []  # 需要修改的文件
        self.del_files = list(self._local_files - self._remote_files)  # 需要删除的文件
        self.add_dirs = list(self._remote_dirs - self._local_dirs)  # 需要增加的文件夹
        self.del_dirs = list(self._local_dirs - self._remote_dirs)  # 需要删除的文件夹

        # 检查远程与本地文件一致性
        files_num = len(self._remote_files)
        index = 0
        for f in self._remote_files:
            self._callback("fetch", index, files_num)
            index += 1
            # 文件存在则校验，否则无需校验添加到更改列表
            path = "{}/{}".format(self.local_path, f)
            if not os_exists(path):
                self.change_files.append(f)
            else:
                if self.remote_path:  # 防止远程路径为空时报错
                    url = "{}/{}{}".format(self.git_raw, self.remote_path, f)
                else:
                    url = "{}{}".format(self.git_raw, f)
                remote_hash = self._remote_hash(url, self.headers)
                if remote_hash is None:
                    print("[ERROR] An error occurred while verifying the remote file hash.")
                    return None
                else:
                    if remote_hash != self._local_hash(path):
                        self.change_files.append(f)
        self._callback("fetch", index, files_num)  # 检查完成
        return self.change_files, self.del_files, self.add_dirs, self.del_dirs

    def _callback(self, msg, done, total):
        """
        进度表示回调函数

        Args:
            msg: 消息
            done: 已完成
            total: 总计
        """
        if self.callback:
            self.callback(msg, done, total)

    def clear(self):
        """
        清理临时文件
        """
        if os_exists(self.cache_path):
            os_removedirs(self.cache_path)
            return True
        else:
            return False

    def fetch(self):
        """
        检查是否有新版本

        Returns:
            List: 有新版本
            List: 无新版本
            None: 出现网络错误
        """
        self.clear()
        self.last_time = None
        self.changes = self._check_all()
        if self.changes is None:
            print("[ERROR] Failed to fetch updates, Please check the network.")
        else:
            self.last_time = time.time()
        return self.changes

    def update(self):
        """
        检查并更新

        Returns:
            Ture 成功
            False 不需要
            None 失败
        """
        if self.last_time and self.last_time + 90 >= time.time():  # 90秒内使用上次检查更新的缓存，减小再次检查所消耗的时间
            pass
        else:
            self.last_time = None
            self.changes = self._check_all()
        if self.changes and self.changes != ([], [], [], []):  # 存在不一致的文件
            self.clear()  # 清理缓存文件
            # 创建文件缓存临时目录
            if not os_exists(self.cache_path):
                os_makedirs(self.cache_path)
            # 下载文件到缓存目录
            files_num = len(self.change_files)
            index = 0
            for f in self.change_files:
                self._callback("update", index, files_num)
                index += 1
                file_dir = '/'.join(f.strip('/').split('/')[:-1]).strip('/')  # 获取文件所在目录
                file_dir = "{}/{}".format(self.cache_path, file_dir)
                if not os_exists(file_dir):  # 创建文件目录
                    os_makedirs(file_dir)
                if self.remote_path:  # 防止远程路径为空时报错
                    url = "{}{}/{}".format(self.git_raw, self.remote_path, f)
                else:
                    url = "{}{}".format(self.git_raw, f)
                file = "{}/{}".format(self.cache_path, f)
                if not self._download_file(url, file, self.headers):  # 下载失败
                    # self.clear()  # 清理缓存文件
                    return None
                elif self.check:  # 下载成功校验
                    if self._remote_hash(url, self.headers) != self._local_hash(file):
                        print("[ERROR] File verification failed, update failed.")
                        return None
            self._callback("update", index, files_num) # 更新完成
            # 创建文件夹
            for _dir in self.add_dirs:
                dir_path = "{}/{}".format(self.cache_path, _dir)
                if not os_exists(dir_path):  # 创建文件夹
                    os.mkdir(dir_path)
            # -- 在此之后断电可能出现异常 -- #
            # 删除文件
            for del_file in self.del_files:
                path = "{}/{}".format(self.local_path, del_file)
                if os_exists(path):
                    os.remove(path)
            # 删除文件夹
            for del_dir in self.del_dirs:
                path = "{}/{}".format(self.local_path, del_dir)
                if os_exists(path):
                    os_removedirs(path)
            # 将缓存目录移动至目标位置
            os_movefiles(self.cache_path, self.local_path)
            # -- 在此之前断电可能出现异常 -- #
            self.clear()  # 清理缓存文件
            return True
        else:
            return False
