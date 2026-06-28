# reelsmith — 让 AI 帮你把视频自动剪成精华短片

reelsmith 是给 AI 助手用的一份"剪辑说明书"。你把一段录屏、会议录像,或者一堆手机/相机拍的视频丢给 AI,它就能帮你**自动挑出精彩片段、加上标题和字幕、拼成一个干净的短片**——你不用会任何剪辑软件,也不用自己动手。

> An "agent skill" that lets an AI assistant turn your raw recordings or clips into a polished highlight video — auto-selecting the good parts, adding a title and subtitles. No editing skills required.

## 它能帮你做什么

- 从一段长视频、或一堆零散片段里**自动挑出精华**
- 加上**片头标题**和**字幕**
- 拼成一个成片视频(MP4 文件),手机、电脑都能直接播放,也能发抖音 / 小红书 / 朋友圈
- 想做加长版、想再插一段新素材、想配背景音乐、想换字幕——再说一句话就行

## 怎么用(很简单)

装好之后,直接对你的 AI 助手**说人话**就行,比如:

- “把这段会议录屏剪个一分钟的精华”
- “这几个旅游视频,挑好看的拼成一个短片,放到下载文件夹”
- “再做一个加长版” / “把这段也剪进去” / “配个背景音乐”

AI 会自己看画面、挑片段、配字幕,然后把成片交给你。

## 它有什么不一样

很多类似工具,把作者那台电脑的设置写死了,换一台机器就报错。reelsmith **每次开工前会先自动检查你的电脑**(装了哪些工具、有什么字体、能不能用硬件加速),再挑最稳、最快的做法。所以它在不同电脑上都更不容易坏。

## 需要先装两个免费工具(一次就够)

把下面两行,粘到电脑的"终端"里回车即可(以 Mac 为例):

```bash
brew install ffmpeg
python3 -m pip install Pillow
```

- **ffmpeg**:免费开源的视频处理引擎,真正"动手剪"的就是它
- **Pillow**:用来把字幕做成文字图片

## 安装 reelsmith

下载到 AI 助手的技能目录即可:

```bash
git clone https://github.com/charleshan7/reelsmith.git \
  ~/.claude/skills/reelsmith
```

## 小贴士

- 成品是一个 **MP4 视频文件**,可以直接发布,也能再拖进任何剪辑软件继续加工。
- 处理 4K 这种大视频会比较慢,它会自动用硬件加速(如果你的电脑支持)。
- 默认横屏 16:9;需要竖屏(适合抖音/小红书)也可以,跟 AI 说一声。

## 文件说明(给好奇的人)

```
reelsmith/
├── SKILL.md          # 给 AI 读的主流程
├── scripts/
│   ├── detect_env.sh # 自动检查电脑环境
│   └── render_text.py # 把文字做成字幕图片
├── LICENSE
└── README.md
```

## License

MIT — 见 [LICENSE](LICENSE)。作者:feifeidouya
