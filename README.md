# API调用平台

一个简易的API调用平台，后端作为代理执行前端提交的API请求，并把结果返回给前端。

可以预先写好`json`或`py`文件，放到`storage`目录，后端启动时会扫描目录并生成目录结构，在前端可以打开预先写好的文件并执行。

支持命名空间和变量，保存在`namespace.json`里面。

![screenshot](screenshot.png)
