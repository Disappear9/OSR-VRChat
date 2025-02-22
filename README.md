# OSR-VRChat

一个OSR机器人的驱动程序，实现了OSR机器人与VRChat的动作同步。到点了，开E!!!!

非常感谢[Shocking-VRChat](https://github.com/VRChatNext/Shocking-VRChat)项目搭建的框架！

测试QQ群：1034983762






## 使用方法

### 1.准备工作

确保攻方的牛牛和受方的插座**都是基于SPS制作的**（**不支持DPS/TPS**，因为这两个插件缺少用于计算深度的OGB数据接口）

确认VRChat中开启了OSC数据接口

**Chrome**浏览器打开[Mosa控制器](https://trymosa.netlify.app/)网页，左侧选择Serial并在弹窗中选择对应的串口，拖动控制轴，确保OSR设备工作正常，测试完必须**关闭网页**以解除串口占用

### 2.程序使用



## Q&A

### 1. 什么是OSR？

OSR是**O**pen-source **S**troker **R**obot的缩写，意思是开源飞机杯机器人。目前此项目仅支持OSR2/2+，是OSR系列中最便携小巧的型号，支持2/3轴上的运动。未来将陆续更新对OSR6以及其他更复杂的机器人的支持。更多信息可以参考[此网页](https://discuss.eroscripts.com/t/guide-what-is-the-osr2-sr6-ssr1-and-how-do-i-get-one/158805)。


### 2. 如何获取OSR2设备？

在闲鱼上有很多买成品设备的商家，价格通常和舵机质量/扭矩以及包含的附件有关，可以根据自己的需求以及预算进行购买。如果想自己搭建OSR2系统，请参考[此项目](https://www.patreon.com/tempestvr)。

### 3. 什么是OGB？

[OGB](https://osc.toys/)项目的全名是Osc Goes Brrr，实现了游戏中SPS插入动作和支持[Intiface](https://intiface.com/)的玩具的同步。OGB的作者Senky也是SPS系统的作者，在SPS插件中预留了一系列地址为`/avatar/parameters/OGB/*`的OSC数据接口，大大方便了深度的计算。