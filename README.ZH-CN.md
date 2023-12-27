[English (英语)](./README.md)
# micropython-easyota
- 适用于 `micropython` 的 OTA 更新库，高效，易用，拥有一定的可靠性

### 特点
- 支持 `Github` / `Gitee` 存储库
- 使用单独的缓存目录来缓存文件，最后进行安装，由于安装速度很快，可以极大概率避免更新时断电造成的程序不完整
- 可以指定本地路径和远程路径，支持自动扫描所有文件，也可以手动指定需要更新的文件，自动扫描时也可以忽略指定文件
- 将 `cached_files` 参数设为 `False` 则不会于检查更新时下载文件，只校验哈希，之后更新时会下载文件并进行校验，拥有更高的可靠性，但是更新速度较慢
### 兼容性
- 通过测试的硬件：`ESP32-C3 RAM-400KB Flash-4MB`
- 其他硬件尚未进行测试

### 使用示例
```python
# import machine
from lib.easyota import EasyOTA
from lib.easynetwork import Client

# 连接网络
client = Client()
client.connect('ssid', 'password')
while not client.isconnected():
    pass
print("IP Address: ", client.ifconfig()[0])


# 用于表示更新进度的回调函数
def callback(msg, done, total):
    if msg == "preparation":
        print("准备中:", "{}/{}".format(done, total), "({}%)".format(int(done / total * 100)))
    elif msg == "fetch":
        print("检查更新:", "{}/{}".format(done, total), "({}%)".format(int(done / total * 100)))
    elif msg == "update":
        print("安装更新:", "{}/{}".format(done, total), "({}%)".format(int(done / total * 100)))


# 初始化实例
eo = EasyOTA('funnygeeker', 'micropython-easyota', 'main',
             git_raw=EasyOTA.GITHUB_RAW, git_api=EasyOTA.GITHUB_API,
             ignore=['/lib/easynetwork.py', '/lib/urequests.py', '/lib/easyota.py', '/main.py'],
             callback=callback)  # 更多使用方法详见注释，您可以用 AI 将注释翻译为您所使用的语言


# 在检查更新之前，请确保您的开发板已经连接到互联网，否则可能会报错。
# 如果您使用的是 Thonny IDE 进行调试，拷贝文件后，别忘记切换到设备的根目录，否则路径可能不正确，无法正常进行更新
result = eo.fetch()  # 检查更新
if result:
    print("""===【检查更新】===
更改的文件：\n{}
删除的文件：\n{}
新增的目录：\n{}
删除的目录：\n{}
""".format(result[0], result[1], result[2], result[3]))


result = eo.update()  # 更新文件
if result is True:
    result = '更新成功'
    # machine.reset()  # 重启开发板
elif result is False:
    result = '无需更新'
elif result is None:
    result = '更新失败'
if result:
    print("===【更新结果】===\n{}".format(result))
# 记得在 Thonny IDE 中点击 刷新，以刷新文件列表
```
### 注意事项
- 更新过程中下载的文件会缓存到缓存目录，更新前请注意开发板的可用存储空间是否足够
- 更新成功后建议及时重启开发板，以避免现有的程序被更改，在 `import` 时引发一些 `BUG`
- 该程序不适用于文件非常多的情况检查更新，若文件列表过大，在低性能开发板上可能会引发内存分配错误
- 使用时需要连接网络，您可以使用 [https://github.com/funnygeeker/micropython-easynetwork](https://github.com/funnygeeker/micropython-easynetwork) 连接无线网络，也可以用其他的方式完成网络的连接。
- `Github` 仓库在国内使用时如果经常出现网络问题，请使用 `EasyOTA.GITHUB_RAW2` 进行测试，或者更换为 `Gitee` 存储库进行测试
- 您仍然需要留意正好处于两次版本切换之间进行更新的用户，可以试着将版本文件与程序分开进行更新，先更新版本文件，版本文件里的更新选项设为禁用更新，2-6小时后再更新程序，将版本说明文件里的更新选项设为启用更新，以达到最佳的可靠性

### 灵感来源
Senko：[https://github.com/RangerDigital/senko](https://github.com/RangerDigital/senko)
