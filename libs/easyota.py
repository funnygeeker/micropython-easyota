import os
import time
import hashlib
import binascii
from libs import urequests


def get_path_type(path: str):
    """
    判断路径类型

    Args:
        path: 路径

    Returns:
        'dir': 如果路径是目录
        'file': 如果路径是文件
    """
    try:
        result = os.stat(path)  # 获取路径的信息
        return "dir" if result[0] & 0o170000 == 0o040000 else "file"  # 如果是目录返回'dir'，如果是文件返回'file'
    except OSError:  # 路径不存在或无法访问
        return None


def make_dirs(path: str):
    """
    逐级创建目录

    Args:
        path: 路径
    """
    # 分割路径为目录名列表
    folders = path.strip("/").split("/")
    # 逐级创建目录
    for i in range(len(folders)):
        folder = "/".join(folders[:i + 1])
        if not exists(folder):
            os.mkdir(folder)


def move_files(old: str, new: str):
    """
    移动目录下的所有文件到另一个目录

    Args:
        old: 原目录路径
        new: 目标目录路径
    """
    old = old.rstrip("/")
    new = new.rstrip("/")
    dirs = os.listdir(old)
    for d in dirs:
        try:
            os.rename("{}/{}".format(old, d), "{}/{}".format(new, d))
        except:  # 移动的是文件夹，且文件夹已存在，则尝试单独移动里面的文件
            move_files("{}/{}".format(old, d), "{}/{}".format(new, d))


def remove_dirs(path: str):
    """
    逐级删除目录

    Args:
        path: 目录路径
    """
    for file in os.listdir(path):
        file_path = "{}/{}".format(path, file)
        if get_path_type(file_path) == "dir":
            remove_dirs(file_path)  # 递归删除子目录
        else:
            os.remove(file_path)  # 删除文件
    os.rmdir(path)  # 删除目录本身


def is_dir(path: str) -> bool:
    """
    判断路径是否为文件夹

    Args:
        path: 路径

    Returns:
        True or False
    """
    return get_path_type(path) == "dir"


def is_file(path: str) -> bool:
    """
    判断路径是否为文件

    Args:
        path: 路径

    Returns:
        True or False
    """
    return get_path_type(path) == "file"


def exists(path: str) -> bool:
    """
    判断路径是否存在

    Args:
        path: 路径

    Returns:
        True：如果路径存在
        False：如果路径不存在
    """
    try:
        os.stat(path)
        return True
    except OSError:  # 路径不存在
        return False


def lstrip(string: str, chars: str):
    """
    清除字符串左边的指定字符（完全匹配）

    Args:
        string: 原始文本
        chars: 要清除的字符

    Returns:
        处理后的文本
    """
    chars_len = len(chars)
    if string[:chars_len] == chars:
        string = string[chars_len:]
    return string


def rstrip(string: str, chars: str):
    """
    清除字符串右边的指定字符（完全匹配）

    Args:
        string: 原始文本
        chars: 要清除的字符

    Returns:
        处理后的文本
    """
    chars_len = len(chars)
    if string[-chars_len:] == chars:
        string = string[:-chars_len]
    return string


def strip(string: str, chars: str):
    """
    清除字符串左右两边的指定字符（完全匹配）

    Args:
        string: 原始文本
        chars: 要清除的字符

    Returns:
        处理后的文本
    """
    string = lstrip(string, chars)
    return rstrip(string, chars)


def decode_hash(sha1_hash):
    """
    Hash 解码为文本
    Args:
        sha1_hash: SHA-1 哈希值
    Returns:
        解码后的文本
    """
    return binascii.hexlify(sha1_hash).decode("utf-8")


class EasyOTA:
    GITHUB_API = "https://api.github.com/repos/{user}/{repo}/git/trees/{branch}?recursive=1"
    GITHUB_RAW = "https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
    GITHUB_RAW2 = "https://raw.fastgit.org/{user}/{repo}/{branch}/{path}"
    GITEE_API = "https://gitee.com/api/v5/repos/{user}/{repo}/git/trees/{branch}?recursive=1"
    GITEE_RAW = "https://gitee.com/{user}/{repo}/raw/{branch}/{path}"
    USER_AGENT = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/"
                      "537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.49"
    }

    def __init__(
            self,
            user: str,
            repo: str,
            branch: str,
            files: list = None,
            ignore: list = None,
            git_raw: str = None,
            git_api: str = None,
            local_path: str = "",
            remote_path: str = "",
            cache_path: str = "/_EasyOTA_Cache",
            callback=None,
            headers: dict = None,
            cached_files: bool = True,
    ):
        """
        初始化 EasyOTA 实例

        Args:
            user: 用户名
            repo: 存储库
            branch: 分支，一般为 `main` 或者 `master`
            files: 需要检查的文件和路径，以 local_path 为标准的相对目录，默认：检查全部
            ignore: 不需要检查的文件，以 local_path 为标准的相对目录，默认：无
            git_raw: Git 原始文件下载地址
            git_api: Git 文件信息 API 地址
            local_path: 需要检查的本地目录
            remote_path: 需要检查的远程 (Git) 目录
            cache_path: EasyOTA 的数据缓存目录
            callback: 回调函数，用于返回检查状态和进度 Return: ("msg", done, total)，done 和 total 为整数，msg 为字符串：
                preparation: 正在准备中
                fetch: 正在检查更新
                update: 正在安装更新
            headers: requests 请求头
            cached_files: 检查更新时，缓存更新文件
                True：检查更新时会缓存文件在本地，检查完成后可以立刻安装更新，可以快更新的速度
                False：更新文件需要在检查和更新时各下载和校验一遍，由于校验了两次哈希，拥有更高的可靠性，但是更新失败的概率和所需的时间为两倍

        Notes:
            检查更新前，请先确保设备的存储空间足够安装更新，否则，设备可能会出错
            EasyOTA 虽然拥有一定的可靠性，但是您仍然需要留意正好处于两次版本切换之间进行更新的用户，可以试着将版本文件与程序分开进行更新，先更新
            版本文件，版本文件里的更新选项设为禁用更新，2-6小时后再更新程序，将版本说明文件里的更新选项设为启用更新，以达到最佳的可靠性
        """
        self.local_dirs = None
        self.local_files = None
        self.remote_files = None
        self.files = files or []
        self.ignore = ignore or []
        self.git_raw = git_raw or EasyOTA.GITHUB_RAW
        self.git_api = git_api or EasyOTA.GITHUB_API
        self.cache_path = cache_path.strip("/")
        self.local_path = local_path.strip("/")
        self.remote_path = remote_path.strip("/")
        self.git_raw = self.git_raw.format(user=user, repo=repo, branch=branch, path=self.remote_path).strip("/")
        self.git_api = self.git_api.format(user=user, repo=repo, branch=branch)
        self.changes = []  # 需要进行更新的文件
        self.callback = callback
        self.check_time = None  # 上一次更新检查时间
        self.deleted_dirs = None
        self.added_dirs = None
        self.deleted_files = None
        self.changed_files = None
        self.headers = headers or self.USER_AGENT
        self.cached_files = cached_files
        self.ignore = [i.lstrip('/') for i in self.ignore]

    def list_files(self, path: str, level: int = 100, _level: int = 1, relative_path: str = '') -> tuple:
        """
        分别列出所有文件和目录（输出相对目路径）

        Args:
            path: 起始目录
            level: 最大文件夹层数
            _level: 当前所在的文件夹层数（一般不需要修改）
            relative_path: 相对路径（输出为相对当前路径的路径列表）

        Returns:
            Tuple[file_paths(list), dir_paths(list)]
        """
        files = []  # 文件列表
        dirs = []  # 目录列表
        local_path = "{}/".format(relative_path.strip("/"))
        if not exists(path):
            print('[ERROR] EasyOTA: local_path "{}" not exists.'.format(path))
        items = os.listdir(path)
        for item in items:
            _path = "{}/{}".format(path, item)
            if is_dir(_path):
                dirs.append(lstrip(_path, local_path))
                if _level <= level:
                    files_list, dirs_list = self.list_files(_path, level, _level + 1)
                    files.extend(files_list)
                    dirs.extend(dirs_list)
            elif is_file(_path):
                files.append(lstrip(_path, local_path))
        return files, dirs

    @staticmethod
    def download_file(url: str, file: str, headers: dict, retry: int = 3):
        """
        下载文件到指定路径

        Args:
            url: 远程文件 URL
            file: 文件存储在本地的路径
            headers: User-Agent
            retry: 最大重试次数

        Returns:
            True: 成功
            None: 失败
        """
        num = 0
        response = None
        while num <= retry:
            try:
                response = urequests.get(url, headers=headers, stream=True)
                if response.status_code != 200:
                    raise Exception("Status Code - {}".format(response.status_code))
                data = response.raw.read(2048)
                # 路径不存在则自动创建
                path = "/".join(file.split("/")[:-1])
                if path.rstrip("/"):
                    make_dirs(path)
                # 下载文件
                with open(file, "wb") as f:
                    while data:
                        f.write(data)
                        data = response.raw.read(2048)
                return True
            except Exception as e:
                print("[WARN] EasyOTA: File Download Failed: {}".format(e))
                num += 1
            finally:
                if response:
                    response.close()
        return None

    @staticmethod
    def calculate_local_hash(file: str) -> str:
        """
        计算本地文件哈希值

        Args:
            file: 文件路径

        Returns:
            SHA-1 哈希值
        """
        with open(file, "rb") as f:
            _hash = hashlib.sha1()
            data = f.read(2048)
            while data:
                _hash.update(data)
                data = f.read(2048)
        return decode_hash(_hash.digest())

    @staticmethod
    def calculate_remote_hash(url: str, headers: dict, retry: int = 3):
        """
        校验远程文件（服务器端文件）的哈希

        Args:
            url: 文件链接
            headers: requests 请求头
            retry: 最大重试次数

        Returns:
            hex 哈希结果
        """
        num = 0
        response = None
        while num <= retry:
            try:
                _hash = hashlib.sha1()
                response = urequests.get(url, headers=headers, stream=True)
                if response.status_code != 200:
                    raise Exception("Status Code - {}".format(response.status_code))
                data = response.raw.read(2048)
                # 下载文件
                while data:
                    _hash.update(data)
                    data = response.raw.read(2048)
                return decode_hash(_hash.digest())
            except Exception as e:
                print("[WARN] EasyOTA: File to Verify Remote File Hash: {}".format(e))
                num += 1
            finally:
                if response:
                    response.close()
        return None

    def _check_all(self):
        """
        检查全部文件的一致性
        Returns:
            一个包含下列四个列表的元组:
                - changed_files: 需要更改的文件 [{'path':'/xxx/xx', 'sha1': 'xxxxx'}]
                - deleted_files: 需要删除的文件路径列表
                - added_dirs: 需要添加的目录路径列表
                - deleted_dirs: 需要删除的目录路径列表
        """
        # 确定需要进行更新的目录和文件 #
        self.local_files = set()
        self.local_dirs = set()
        self.perform_callback("preparation", 20, 100)
        if self.files:  # 指定文件和路径
            for f in self.files:
                f = f.strip("/")
                if f:  # 过滤空路径（过滤根目录）
                    path = "{}/{}".format(self.local_path, f).strip("/")
                    for i in self.ignore:  # 检查文件是否为忽略的路径内
                        if path.startswith(i):
                            break
                    else:
                        if is_file(path):
                            self.local_files.add(f)  # 添加到要同步的文件
                        elif is_dir(path):
                            self.local_dirs.add(f)  # 添加到要同步的目录

        else:  # 所有文件和路径
            files, dirs = self.list_files(self.local_path, relative_path=self.local_path)  # 列出本地所有文件和目录
            for f in files:
                f = f.strip("/")
                path = "{}/{}".format(self.local_path, f).strip("/")
                for i in self.ignore:
                    if path.startswith(i):
                        break
                else:
                    self.local_files.add(f)  # 添加到要同步的文件
            self.perform_callback("preparation", 40, 100)
            for d in dirs:
                d = d.strip("/")
                path = "{}/{}".format(self.local_path, d).strip("/")
                for i in self.ignore:  # 文件夹不被忽略且不属于被忽略的目录内
                    if path.startswith(i):
                        break
                else:
                    self.local_dirs.add(d)

        # Git 仓库已有且需要同步的目录和文件 #
        self.remote_files = set()
        self.remote_dirs = set()
        # 请求 Git 存储库 API，获取文件列表
        num = 0
        self.perform_callback("preparation", 60, 100)
        while num < 2:  # 最大重试 2 次
            try:
                response = urequests.get(self.git_api, headers=self.headers)
                if response.status_code == 200:
                    for f in response.json()["tree"]:
                        path = lstrip(f["path"].strip("/"), self.remote_path).strip("/")
                        if f["path"].strip("/").startswith(self.remote_path) and path:  # 筛选指定路径，过滤路径为空的情况
                            if f["type"] == "blob":  # 是文件，且不属于被忽略的文件夹内
                                for i in self.ignore:
                                    if path.startswith(i):
                                        break
                                else:
                                    self.remote_files.add(path)
                            elif f["type"] == "tree":  # 是目录，且不被忽略
                                for i in self.ignore:
                                    if path.startswith(i):
                                        break
                                else:
                                    self.remote_dirs.add(path)
                            else:
                                pass  # 路径类型不支持，或不需要更新
                    break
                else:
                    raise OSError("Status Code - {}".format(response.status_code))
            except Exception as e:
                num += 1
                print("[WARN] EasyOTA: API request failed: {}".format(e))
                time.sleep(1)
        else:
            return None

        self.perform_callback("preparation", 80, 100)

        if self.files:  # 若指定需要更新的文件范围，则进行计算
            files_set = set(self.files)
            self.local_files &= files_set
            self.remote_files &= files_set
            self.remote_dirs &= files_set
            self.local_dirs &= files_set
        self.deleted_files = list(self.local_files - self.remote_files)  # 需要删除的文件
        self.added_dirs = list(self.remote_dirs - self.local_dirs)  # 需要增加的文件夹
        self.deleted_dirs = list(self.local_dirs - self.remote_dirs)  # 需要删除的文件夹
        self.changed_files = []  # 需要修改的文件 [{'path':'/xxx/xx', 'sha1': 'xxxxx'}]
        # 检查远程与本地文件一致性 #
        self.perform_callback("preparation", 100, 100)
        total_files = len(self.remote_files)  # 总远程文件数量
        done_files = 0
        for f in self.remote_files:  # 这里的 f 为相对路径，使用时按需转换为绝对路径
            f = f.strip("/")
            # 获取哈希
            url = "{}/{}".format(self.git_raw, f)
            # 检查文件更新
            file_dir = "/".join(f.strip("/").split("/")[:-1]).strip("/")  # 文件的所在目录的绝对路径
            file_dir = "{}/{}".format(self.cache_path, file_dir)  # 文件下载到工作文件夹的绝对路径
            file = "{}/{}".format(self.cache_path, f)  # 文件在缓存目录的绝对路径
            local_file = "{}/{}".format(self.local_path, f)  # 文件的本地绝对路径
            if exists(local_file):
                local_hash = self.calculate_local_hash(local_file)
            else:
                local_hash = 0
            self.perform_callback("fetch", done_files, total_files)
            done_files += 1
            if self.cached_files:  # 检查更新时缓存文件
                if not exists(file_dir):  # 创建文件目录
                    make_dirs(file_dir)
                if self.download_file(url, file, self.headers) is None:  # 下载文件失败
                    return None
                remote_hash = self.calculate_local_hash(file)
                if remote_hash != local_hash:  # 哈希不一致则加入需要修改的文件
                    self.changed_files.append({"path": f, "sha1": remote_hash})
                else:
                    os.remove(file)  # 删除哈希一致的文件，减小存储空间占用
            else:  # 检查更新时不缓存文件
                remote_hash = self.calculate_remote_hash(url, self.headers)
                if remote_hash is None:
                    return None
                if remote_hash != local_hash:
                    self.changed_files.append({"path": f, "sha1": remote_hash})
        total_files = total_files if total_files else 1  # total_file 不为 0
        self.perform_callback("fetch", total_files, total_files)  # 检查完成
        return (
            self.changed_files,  # 修改的文件
            self.deleted_files,  # 删除的文件
            self.added_dirs,  # 添加的目录
            self.deleted_dirs,  # 删除的目录
        )

    def perform_callback(self, msg, done, total):
        """
        进度表示回调函数

        Args:
            msg: 消息
                准备中：preparation
                检查中：fetch
                更新中：update
            done: 已完成
            total: 总计
        """
        if self.callback:
            try:
                self.callback(msg, done, total)
            except Exception as e:
                print("[ERROR] EasyOTA: Callback Function ERROR - {}".format(e))

    def clear(self):
        """
        清理临时文件
        Returns:
            True：成功清理缓存文件
            False：缓存文件不存在
        """
        if exists(self.cache_path):
            remove_dirs(self.cache_path)
            return True
        else:
            return False

    def fetch(self):
        """
        检查是否有新版本

        Returns:
            List: 有新版本 (if list)
            List: 无新版本 (if not list)
            None: 出现网络错误
        """
        self.clear()
        self.check_time = None
        self.changes = self._check_all()
        if self.changes is None:
            print("[ERROR] EasyOTA: Failed to fetch updates.")
            return None
        else:
            self.check_time = time.time()
        if self.changes == ([], [], [], []):
            self.clear()
        return self.changes

    def update(self):
        """
        检查并更新

        Returns:
            Ture 成功
            False 不需要
            None 失败
        """
        if self.check_time and self.check_time + 180 >= time.time():  # 180秒内使用上次检查更新的缓存，减小再次检查所消耗的时间
            pass
        elif self.check_time and self.cached_files:
            pass
        else:
            self.fetch()
        if self.changes and self.changes != ([], [], [], []):  # 存在不一致的文件
            files_num = len(self.changed_files)  # 修改的文件数量
            files_num = files_num if files_num else 1  # 文件数量不为 0
            index = 0
            if self.cached_files:
                self.perform_callback("update", index, files_num)
            else:
                # 创建文件缓存临时目录
                if not exists(self.cache_path):
                    make_dirs(self.cache_path)
                # 下载文件到缓存目录
                for f in self.changed_files:
                    file, _hash = f["path"], f["sha1"]
                    self.perform_callback("update", index, files_num)
                    index += 1
                    file_dir = "/".join(file.strip("/").split("/")[:-1]).strip("/")  # 获取文件所在目录
                    file_dir = "{}/{}".format(self.cache_path, file_dir)
                    if not exists(file_dir):  # 创建文件夹
                        make_dirs(file_dir)
                    url = "{}/{}".format(self.git_raw, file)
                    file = "{}/{}".format(self.cache_path, file)
                    retry = 0
                    while retry < 2:
                        self.download_file(url, file, self.headers)
                        if not exists(file) or self.calculate_local_hash(file) != _hash:
                            print("[WARN] EasyOTA: File verification failed, retrying...")
                        else:
                            break
                        retry += 1
                    else:
                        print("[ERROR] EasyOTA: Update Failed!")
                        return None
            # -- 对文件进行更改中，不要断电 -- #
            # 创建新文件夹
            for _dir in self.added_dirs:
                dir_path = "{}/{}".format(self.local_path, _dir)
                if not exists(dir_path):  # 创建文件夹
                    os.mkdir(dir_path)
            # 删除文件
            for del_file in self.deleted_files:
                path = "{}/{}".format(self.local_path, del_file)
                if exists(path):
                    os.remove(path)
            # 删除文件夹
            for del_dir in self.deleted_dirs:
                path = "{}/{}".format(self.local_path, del_dir)
                if exists(path):
                    remove_dirs(path)
            # 将缓存目录移动至目标位置
            move_files(self.cache_path, self.local_path)
            # -- 对文件进行更改中，不要断电 -- #
            self.perform_callback("update", files_num, files_num)  # 更新完成
            self.clear()  # 清理缓存文件
            return True
        else:
            return False
