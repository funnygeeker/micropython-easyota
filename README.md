[简体中文 (Chinese)](./README.ZH-CN.md)
# micropython-easyota

- OTA update library for `micropython`, efficient, easy to use, and with a certain level of reliability.

### Features
- Supports `Github` / `Gitee` repositories.
- Uses a separate cache directory to store downloaded files and installs them at the end. Due to the fast installation speed, it can greatly reduce the likelihood of incomplete programs caused by power interruptions during the update process.
- Can specify both local and remote paths. Supports automatic scanning of all files, and can also manually specify the files to update. It is also possible to ignore specific files during automatic scanning.
- Setting the `cached_files` parameter to `False` will not download files during the update check, only verify the hash. The files will be downloaded and verified during the update process, providing higher reliability but slower update speed.

### Compatibility
- Tested hardware: `ESP32-C3 RAM-400KB Flash-4MB`.
- Other hardware has not been tested.

### Usage Example
```python
# import machine
from lib.easyota import EasyOTA
from lib.easynetwork import Client

# Connect to the network
client = Client()
client.connect('ssid', 'password')
while not client.isconnected():
    pass
print("IP Address: ", client.ifconfig()[0])

# Callback function to represent the update progress
def callback(msg, done, total):
    if msg == "preparation":
        print("Preparing:", "{}/{}".format(done, total), "({}%)".format(int(done / total * 100)))
    elif msg == "fetch":
        print("Checking for updates:", "{}/{}".format(done, total), "({}%)".format(int(done / total * 100)))
    elif msg == "update":
        print("Installing update:", "{}/{}".format(done, total), "({}%)".format(int(done / total * 100)))

# Initialize the instance
eo = EasyOTA('funnygeeker', 'micropython-easyota', 'main',
             git_raw=EasyOTA.GITHUB_RAW, git_api=EasyOTA.GITHUB_API,
             ignore=['/lib/easynetwork.py', '/lib/urequests.py', '/lib/easyota.py', '/main.py'],
             callback=callback)  # More usage details can be found in the comments. You can use AI to translate the comments to your desired language.

# Before checking for updates, make sure your development board is connected to the internet, otherwise it may throw an error.
# If you are using Thonny IDE for debugging, after copying the files, don't forget to switch to the root directory of the device, otherwise the path may not be correct and the update process won't work properly.
result = eo.fetch()  # Check for updates
if result:
    print("""===【Check for Updates】===
Modified files:\n{}
Deleted files:\n{}
New directories:\n{}
Deleted directories:\n{}
""".format(result[0], result[1], result[2], result[3]))

result = eo.update()  # Update files
if result is True:
    result = 'Update successful'
    # machine.reset()  # Restart the development board
elif result is False:
    result = 'No update needed'
elif result is None:
    result = 'Update failed'
if result:
    print("===【Update Result】===\n{}".format(result))
# Remember to click "Refresh" in Thonny IDE to update the file list.

# machine.reset()  # Restart the development board to apply the update
```

### Notes
- The files downloaded during the update process are cached in the cache directory. Before updating, make sure that the available storage space on your development board is sufficient.
- After a successful update, it is recommended to restart the development board promptly to avoid changes to the existing program that can cause bugs when importing modules.
- This program is not suitable for cases where there are a large number of files to check for updates. If the file list is too large, it may cause memory allocation errors on low-performance development boards.
- Network connection is required when using this program. You can use [https://github.com/funnygeeker/micropython-easynetwork](https://github.com/funnygeeker/micropython-easynetwork) to connect to a wireless network, or use other methods to establish the network connection.
- If you frequently encounter network issues when using the `Github` repository in China, please test using `EasyOTA.GITHUB_RAW2` or switch to the `Gitee` repository for testing.
- You still need to be cautious if you are updating users who lie exactly between two version switches. You can try updating the version file separately from the program. First update the version file with the update option set to disable updates, and then update the program 2-6 hours later, enabling the update option in the version file to achieve the best reliability.

### Source of inspiration
Senko: [https://github.com/RangerDigital/senko](https://github.com/RangerDigital/senko)