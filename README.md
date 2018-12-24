## 开发说明

- 硬件测试环境: 
    - 树莓派(各版本均支持, 请自行选择)
    - GPIO直插LCD屏或HDMI外接显示器
        - LCD屏刷新率可能受限于驱动方式, 请注意选择和测试
    
- 开发测试环境:
    - VMware 12
    - Raspbian

## 调试步骤

1. 安装VMware
2. 下载镜像 [DEBIAN STRETCH WITH RASPBERRY PI DESKTOP](https://www.raspberrypi.org/downloads/raspberry-pi-desktop/ "下载地址")
3. 安装Raspbian虚拟机, [参考](https://www.jianshu.com/p/1a65cb0b8f58 "安装参考")
4. 虚拟机网卡设为桥接模式, 桥接的物理网卡选择您当前所连接网卡, 这样虚拟机的IP就在您当前的局域网内了
5. 打开虚拟机, 进入Raspbian桌面, 完成基础配置
    - 打开终端, 输入`raspi-config`, 打开SSH功能
    - 如果需使用GPIO屏幕, 请依据总线方式打开SPI等端口
    - 输入`ip addr`, 查看IP地址
6. 使用SSH上传代码(如WinSCP), 默认用户名:pi/raspberry
7. 安装依赖Python库, 使用`pip install xxx`(xxx是以下的模块名)
    - pyudev
    - pyserial
    - pytz
    - pyyaml
    - pygame(Raspbian已预装)
8. 若物理机为Windows系统, 请下载cp210x驱动, 让宿主机能够识别到FT-891
    - [下载地址](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers "cp210x驱动下载地址")
    - 使用USB线连接PC和FT-891, 注意打开VMware右下角的USB设备, 使虚拟机能够识别到cp2102
9. FT-891打开电源, 长按F键, 设置CAT Baudrate=38400
10. 运行代码
    - `python controller.py`

使用树莓派调试请从以上第5步开始

## 代码结构说明

- `rig.py`
    - 设备通信模块, 使用`RIG`类完成设备连接, 以及指令发送
- `controller.py`
    - 使用pygame完成前台界面显示(主线程), `Rig_Polling`线程完成设备轮询, 将设备各参数存入全局变量
- `conf`
    - `custom.yaml`: 设备连接及用户设置
    - `layout.yaml`
        - 界面显示配置, 在主线程中完成资源载入
        - *ELEMENT* 段配置各界面元素使用的图片资源和位置
        - 若需新增分辨率配置, 请将图片资源放在res/{RESOLUTION}路径下, 一个元素的不同状态请垂直排列, *POS*为显示位置, *SIZE*为显示大小, *STAT*为各照片对应的码值
    - `YAESU_CAT3.yaml`
        - 450/891/991/DX系列机型的CAT协议配置
        - 请将功能分解成单一功能进行配置
        - 配置说明参考 `commad_profile_template.yaml`
- `res`
    - 图片资源
    - 建议按分辨率或预设的主题方案进行组织
