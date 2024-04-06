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
