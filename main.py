import machine
from libs.easyota import EasyOTA

eo = EasyOTA('funnygeeker', 'micropython-easyota', 'main', files=['main.py'], ignore=['libs'],
             git_raw=EasyOTA.GITHUB_RAW, git_api=EasyOTA.GITHUB_API)  # 更多使用方法详见注释


def state(msg, done, total):
    if total == 0:
        x = 0
    else:
        x = done / total * 100
    if msg == 'fetch':
        print("检查进度：{}%".format(x))
    elif msg == 'update':
        print("更新进度：{}%".format(x))


eo.callback = state  # 设置回调函数（非必须）

# 在检查更新之前，请确保您的开发板已经连接网络，否则可能会报错。
result = eo.fetch()  # 检查更新
if result:
    print("""===【检查更新】===
更改的文件：{}
删除的文件：{}
新增的目录：{}
删除的目录：{}
""".format(result[0], result[1], result[2], result[3]))

result = eo.update()  # 更新文件
if result is True:
    result = '更新成功'
    machine.reset()  # 重启开发板
elif result is False:
    result = '无需更新'
elif result is None:
    result = '更新失败'
if result:
    print("===【更新结果】===\n{}".format(result))
