# micropython-easyota
！12月前会有一个更新，目前已知一个bug，在修。
- 适用于 `micropython` 的简易 OTA 更新库，相较于 [Senko](https://github.com/RangerDigital/senko)，增加对 OTA 失败等异常情况的处理机制，
以及更多更新选项。
- 比如更新到一半时突然断电，或者文件下载不完整等情况导致的异常都可以很大程度地避免。
- 同时，对于超过内存大小的文件也可以正常地进行下载和更新。
- 可用于 `Github` / `Gitee` 存储库

### 硬件兼容性
- 已通过测试的硬件：`esp32c3 Ram-400KB Flash-4MB`
- 其他硬件尚未进行测试

### 注意事项
- 使用时需要连接网络，在硬件允许的情况下，您可以使用 `micropython-easynetwork` 连接无线网络，也可以用其他的方式完成网络的连接。
- [https://github.com/funnygeeker/micropython-easynetwork](https://github.com/funnygeeker/micropython-easynetwork)
- `Github` 仓库在使用时如果经常出现网络问题，必要时请更换为 `Gitee` 仓库进行测试
- 更新过程中下载的文件会缓存到 `Flash`，更新前请注意开发板的可用存储空间是否足够
- 更新成功后建议及时重启开发板

### 参考资料
Github - Senko：[https://github.com/RangerDigital/senko](https://github.com/RangerDigital/senko)

### 其他
感谢各位大佬对开源做出的贡献！

交流QQ群：[748103265](https://jq.qq.com/?_wv=1027&k=I74bKifU)
