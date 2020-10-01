# DownloadM3U8_Script_V2

## 环境

- Windows 10
- Python 3.7
- Pycharm 2020.1

## 简介

由于上个版本需要使用[N_m3u8DL-CLI](https://github.com/nilaoda/N_m3u8DL-CLI)，而[N_m3u8DL-CLI](https://github.com/nilaoda/N_m3u8DL-CLI)只能在Windows平台使用。所以我又重写了一份脚本。

## 使用方法

> 请安装以下包
> - `pip install m3u8`
> - `pip install pycryptodome`
> 	-  进入python安装目录，如C:\python37
>	-  在\Lib\site-packages目录下找到：
>	-  crypto这个目录重命名为: Crypto
> - `pip install natsort`
> - `pip install dataclasses`
> - `pip install concurrent`
> - `pip install glob`	

打开[全网影片搜索](http://lab.liumingye.cn/)，打开某一集（期）的播放页面，复制地址

![](https://cdn.jsdelivr.net/gh/HowieHye/CDN/img/20200613172607.png)

运行程序，输入地址，根据提示可选择下载的集/期数。

## 致谢

- [刘明野](https://liumingye.cn/)
- [Bajins](https://www.bajins.com/)
