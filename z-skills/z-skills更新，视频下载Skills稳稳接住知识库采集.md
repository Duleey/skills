---
title: "z-skills更新，视频下载Skills稳稳接住知识库采集"
source: "https://mp.weixin.qq.com/s/0JolyCMfQr-O_a9L9mgJ-w"
author:
  - "[[老章很忙]]"
published:
created: 2026-07-07
description:
tags:
  - "clippings"
---
![图片](https://mmbiz.qpic.cn/mmbiz_png/wibWVO7K9lta44AG6e79icYU0kGh6h5V3aQbsia5lty6RKWicsS8Km3zoQlMrXuCnf0T3UqXTuCn2tOw7Tib9SvQWCeg3lVbpXcypW2PWdunficm0/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

大家好，我是 Ai 看视频的老章

前文[我把视频下载做成了一个 Skill，很万能，不小心开源了](https://mp.weixin.qq.com/s?__biz=MzA4MjYwMTc5Nw==&mid=2649015582&idx=1&sn=47972557f950ded9c4e7a3836570f630&token=1833552481&lang=zh_CN&scene=21#wechat_redirect)，很受欢迎，大家提了很多奇怪的需求，不便提及，我这个 skills 远比想象中强大，那些奇怪的视频可以下，但不能说

我这个 skills 显然是用于正经用途的，比如随后开源的[视频总结 Skills 来了](https://mp.weixin.qq.com/s?__biz=MzA4MjYwMTc5Nw==&mid=2649015614&idx=1&sn=d9a701499d9c04a0e3ec4e597304fb49&scene=21#wechat_redirect)，融入了我的很多奇思妙想，但是网友们比我脑洞还大，玩法很多样

不能忘了初心，这个视频下载Skills是从我的[搭建个人知识库，分享一个我原创知识采集 Skills](https://mp.weixin.qq.com/s?__biz=MzA4MjYwMTc5Nw==&mid=2649015003&idx=1&sn=a272b7e2acbb1cd7c22f42d5425a8ddd&token=1548175168&lang=zh_CN&scene=21#wechat_redirect)中抽出来强化后的，原 z-web-pack 的视频处理环节显得太落后了

顺便提下，目前我已经开源了9个Skills，比如之前承诺过的四格漫画

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/wibWVO7K9ltYtzxicefuCsLr3fkJRFCnlr8kicyqNmGhKIpiaZup7B4m4PB2l3dZ2kAgyJaEOKJSJE1jFvuvglzQKynnbeD1kF2qMZDUXpJXtYQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

之前 `z-web-pack` 太能干了，网页正文要采、图片要存、顺手连视频也要下，链接要下钻，下钻之后上面的步骤再拉一遍

刚开始看起来挺爽，一条命令全包

但工具一旦长胖，问题就来了：网页采集本来追求轻、快、稳，视频下载偏偏又重、慢、容易被平台风控卡住

所以这次我做了个拆分：`z-web-pack` 只负责发现视频链接，真正下载统一交给 `z-video-downloader`

### 为什么要拆

我之前写 `1-web-pack` 的时候，确实加过视频下载能力

当时的思路：

- 正文里有 `<video>`、`<source>`、`.mp4` 直链，就流式下载到 `assets`
- 遇到 Ytb、B 站、Vimeo、X、抖音、m3u8，就交给 `yt-dlp`
- 平台报登录、bot、412、cookie，再加 `--browser-cookies chrome` 重试
- 下载成功后，把 Markdown 里的视频链接替换成本地路径

功能完整，却不够强，和网页素材采集的节奏不太一样

采集网页素材，我希望它像扫地机器人，悄悄把正文、图片、链接整理好，失败一两个页面兜底都搞不定的情况下也能继续往下走

视频下载更像搬大件，动不动几百 MB，平台还会查登录态、查 cookie、查 bot，失败原因也复杂很多

这两个动作绑在一起，最后就会出现一个很别扭的体验：我只是想采一份写作资料包，结果它可能因为一个视频链接卡半天

![z-skills 视频职责拆分](https://mmbiz.qpic.cn/sz_mmbiz_png/wibWVO7K9ltZL622L0x19lreWccGq1QvHswObh6Ta7dQjFQVtIbLgtQyANGkrCcW63cdT3FQbMFxD4gH8S49o71ichiafbYGUScv2G5PJUX8m4/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

z-skills 视频职责拆分

### 这次具体改了什么

这次主要动了 4 块

**第一块，改 `z-web-pack/scripts/collect_web_pack. py`**

以前脚本里有一整套视频下载逻辑：

```
--videos direct--videos all--max-video-mb--browser-cookiesdownload_direct_videodownload_platform_videoapply_videos_to_page
```

这些都被清掉了

现在脚本只保留视频链接识别

它会从这些地方抓线索：

- 页面里的 `<video>` 和 `<source>`
- 正文里的 `.mp4`、`.webm`、`.mov` 等直链
- YouTube、B 站、Vimeo、X、TikTok、m3u8 这类平台链接
- 入口本身就是视频页的情况

发现之后写进 `04-media-inventory. md`

清单里会明确标出来：

```
Status: detectedKind: direct / platformDownload Skill: z-video-downloaderSource URL: 原始视频链接
```

这就够了

素材采集阶段只负责把线索留好，下载阶段再由专门工具接手

**第二块，改 `z-web-pack/SKILL. md`**

这是给 Agent 看的说明文件

我把原来那些“视频也下载”“平台视频走 yt-dlp”“浏览器 cookie 重试”的描述删掉了

现在说明里只保留一句核心规则：

```
发现视频链接只记录到 04-media-inventory. md，下载视频请使用 z-video-downloader
```

**第三块，改 `z-video-downloader/SKILL. md`**

`z-video-downloader` 现在是视频下载的唯一承接方

我在它的流程里补了一句：

```
如果链接来自 1-web-pack 的 04-media-inventory. md，直接使用 Source URL 列里的地址
```

这样两个 skill 就接上了

`z-web-pack` 产出线索，`z-video-downloader` 拿线索下载

**第四块，新增项目根目录 `README.md`**

原来 `z-skills` 根目录没有一个总入口

这次顺手补上：

- `z-web-pack` 负责网页素材包采集
- `z-video-downloader` 负责视频下载
- 从这次调整开始，视频链接只进 `04-media-inventory. md`
- 如果要保存视频，把 Source URL 交给 `z-video-downloader`
![z-skills 视频拆分变更流程](https://mmbiz.qpic.cn/sz_mmbiz_png/wibWVO7K9ltbsp4YxQU5Q6LiaXNl2lTZYcY0n7EDZWayMKTg6VCdsgIA9pSS2K5dxKGcIr3WxytElqvzJqRXLhoUCI0KQRJtozYd1Uyvy3zQY/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

z-skills 视频拆分变更流程

### 用法

很简单，大家看上哪个就复制走，或者直接把🔗扔给 Agent 让其帮你安装即可

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/wibWVO7K9ltYnBj5EbZWWCn4N4MALCaYDFAEGD0VvFIvLdh0qToZhPVbqUsGzYdBhJtO4GGKicOD7vFeUxQNaDM91hnEMN1cibianIVG4rRwAGw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)