---
name: reelsmith
description: Use when turning a meeting recording or local video clips (e.g. 腾讯会议/飞书录制、DJI/手机素材) into a highlight package — selecting clips, adding a title card and subtitles, and delivering either a CapCut/剪映 editable draft or a finished MP4. Also use to insert/append extra highlights into an already-rendered cut. Adapts to the local environment instead of assuming fixed paths or tools.
---

# reelsmith — CapCut / 剪映 视频集锦(自适应版)

## 核心原则

**先探测环境,再决定怎么交付。** 不要假设工具、路径、剪映版本、字体——这些因机器而异,而且会过时(剪映新版会加密草稿,旧 skill 在新机器上必然失败)。

两种交付形态,由探测结果决定:
- **剪映工程**(草稿可在 app 里继续编辑)—— 仅当本机剪映草稿是**明文**格式时可行。
- **MP4 成片**(标题/字幕烧进画面)—— 加密剪映 / 工具缺失时的**保底**,任何机器都能成。

## Step 0 — 环境探测(必做,第一步)

```bash
bash scripts/detect_env.sh
```

| 字段 | 据此做什么 |
|---|---|
| `draft_format=plaintext` | 可生成剪映工程(Step 5A) |
| `draft_format=encrypted` | 加密,绕不过 → 只能出 MP4(Step 5B) |
| `draft_format=unknown` | 无现成草稿可判断 → 默认出 MP4;用户坚持要工程,可造一个明文草稿装进草稿箱**实测**能否打开,失败即降级 |
| `ffmpeg_drawtext=no` | 用 `scripts/render_text.py`(PIL)渲染文字 PNG → ffmpeg `overlay` |
| `hwaccel=videotoolbox` | 4K/HEVC 用硬件加速,**快数倍**(见 Step 3) |
| `cjk_font` | 传给 render_text 的 `--font`(脚本本身也会自动回退) |
| `draft_root` / `tool_*` / `disk_free` | 草稿根目录 / 可用工具 / 磁盘余量(4K 工程很占地) |

**把探测结果和"将走哪条交付路线、横屏还是竖屏"明确告诉用户,再开工。** 用户要的形态被环境否决时,说清原因并给替代方案。

## 工作流

### 1. 接入素材 + 建工作目录

输入:腾讯会议/飞书链接,或本地视频路径。建工作目录(用户指定则用之,否则 `~/Documents/video-edits/<项目名>/`):

```text
<workdir>/  source/  clips/  checks/  build/  assets/  edit-plan.md  notes.md
```

飞书录制优先用 lark-minutes / lark-vc 取转写、纪要、媒体;腾讯会议用浏览器/授权下载。**链接受阻就说清卡在哪,用已有本地素材继续。**

### 2. 写 `edit-plan.md`(动刀前必做)

带**具体时间区间**的方案,不能是空泛大纲。无转写时(航拍/空镜)**先抽帧看画面**再定:

```bash
ffmpeg -nostdin -v error -ss "$t" -i "$src" -frames:v 1 -vf scale=480:-1 "checks/thumbs/<id>_<pct>.jpg"
```

方案含:每切片的 源/In/Out/时长/内容/**字幕文案**/输出名,以及**画幅(横屏 1920×1080 或竖屏 1080×1920)**、标题、字幕风格、交付形态。

> **字幕文案是"看图推断"的,不是事实。** 涉及仪式、地名、专有动作(如祈福/上香/点香)时,在 plan 里标注"待确认"并**请用户核对**——别把推断当真写死(实测教训:曾把"点香"误标成"点灯")。

### 3. ffmpeg 切片

先 `ffprobe` 量时长/规格(别猜)。切片(高光重编码精切;4K 源建议降 1080p):

```bash
# hwaccel=videotoolbox 时,加 -hwaccel videotoolbox 解码、用 *_videotoolbox 编码,快数倍:
ffmpeg -nostdin -v error -y -hwaccel videotoolbox -ss "$in" -to "$out" -i "$src" \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" \
  -r 30 -c:v h264_videotoolbox -b:v 10M -pix_fmt yuv420p \
  -c:a aac -ar 48000 -ac 2 -b:a 160k "clips/$name"
# 无硬件加速时回退:-c:v libx264 -preset veryfast -crf 20 (更慢;4K 长段分批切防超时)
```
竖屏 9:16 把 `scale/crop` 改成 `1080:1920`。切完用 `ffprobe` 核对时长。

### 4. 片头标题卡 + 字幕 + 封面

1 秒标题卡开场:定格第一段首帧做背景。**字幕/标题默认白字、底部居中、深色描边**(亮背景可读);别用蓝底大色块,除非用户要。

文字层按 Step 0 分支:`ffmpeg_drawtext=yes` 用 ffmpeg drawtext;否则(常见)用 PIL:

```bash
# 支持自动换行、字体回退、竖屏(--canvas 1080x1920)
python3 scripts/render_text.py "红螺寺祈福 · 2026.6.20" assets/title.png --size 70
python3 scripts/render_text.py "满院许愿祈福" assets/sub02.png --size 60
ffmpeg -nostdin -v error -y -i clips/clip02.mp4 -i assets/sub02.png \
  -filter_complex "[0:v][1:v]overlay=0:0,fps=30,format=yuv420p[v]" \
  -map "[v]" -map "0:a:0" -c:v libx264 -preset veryfast -crf 20 \
  -c:a aac -ar 48000 -ac 2 -b:a 160k build/seg02.mp4   # zsh: 0:a? 的 ? 要加引号
```

### 5A. 生成剪映工程(仅 `draft_format=plaintext`)

> 加密草稿直接跳 5B。手写明文工程装进加密版剪映会报"格式不支持"。

优先 `capcut-cli`/`cutCLI`(若非 MISSING),否则复制本机现有**明文** draft 当模板改 JSON。改前**带时间戳备份**;canvas 按画幅;`duration`=各段微秒和;每段 `target_timerange`(累积起点+时长)、`source_timerange`(0+时长)。复制进 `draft_root` 后在 `root_meta_info.json` 的 `all_draft_store[]` 加一条(`draft_ids` 是**数量**;时间戳**微秒级**)。**剪映运行时不重读且退出会覆盖 root_meta → 顺序必须:退出剪映 → 写登记 → 打开。**

### 5B. 生成 MP4 成片(保底)

标题卡 + 各带字幕段,统一参数(1920×1080 或 1080×1920 / 30fps / h264 yuv420p / aac 48k stereo)后拼接。标题卡补静音音轨(`anullsrc`)才能与有声段 concat:

```bash
printf "file 'seg00.mp4'\nfile 'seg01.mp4'\n..." > build/concat.txt
ffmpeg -nostdin -v error -y -f concat -safe 0 -i build/concat.txt -c copy "成片.mp4"
```
抽帧验收(标题卡 + 每条字幕),逐条确认:**字幕文字与画面内容相符**、无错位、时长符合 plan。

### 6. 增量编辑:把素材插进/接到已有成片

**切完别删 `build/` 分段和 `clips/`** —— 二次编辑全靠它们,几秒就能改。要插入新素材:

1. 按 Step 3/4 把新素材切片、叠字幕,生成新段 `build/seg_x.mp4`(同参数)。
2. 在 concat 列表里把新段放到目标位置(插开头/中间/结尾)。
3. `-c copy` 重拼即可,无需重渲染旧段。
4. 覆盖输出前**备份旧成片**;抽帧验收插入点。

> 同参数(分辨率/帧率/编码/音频采样率)是 `-c copy` 无缝拼接的前提;不一致会拼接失败或卡顿,需重编码统一。

## 可选:背景音乐 / 杂音处理

原声嘈杂(风声/人群)时:加 BGM 并压低或静音环境声。

```bash
# 静音原声、只用 BGM:
ffmpeg -y -i 成片.mp4 -i bgm.mp3 -map 0:v -map 1:a -shortest -c:v copy -c:a aac out.mp4
# 保留环境声但压低,与 BGM 混音(BGM 0.8 / 原声 0.25):
ffmpeg -y -i 成片.mp4 -i bgm.mp3 -filter_complex \
  "[0:a]volume=0.25[a0];[1:a]volume=0.8[a1];[a0][a1]amix=inputs=2:duration=first[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac out.mp4
```

## 可选:剪气口(剪静音)

```bash
ffmpeg -i "$input" -af silencedetect=noise=-38dB:d=0.35 -f null - 2> silence.log
```
按静音时长分档保留(<0.65s 全留;0.65–1.2s 留0.35s;1.2–5s 留0.45s;5–30s 留0.80s;≥30s 留1.20s),重建更紧凑版本。

## Guardrails

- **Step 0 探测先行**,把交付路线 + 画幅讲给用户再动手。
- 切片前必有 `edit-plan.md`;时长用 `ffprobe` 实测;路径/工具/草稿根/字体**一律用探测值,绝不写死别人机器的路径**。
- **字幕推断需用户核对**,仪式/专有动作尤其要确认。
- 改剪映工程 JSON 前必备份;别在剪映开着时改;改完重启剪映。
- 覆盖任何已有成片前先备份;留 `build/`、`clips/` 供二次编辑。
- 源不可访问就如实说,用现有素材继续,不凭空编造切片。
- 最终回复清楚区分:源素材、计划切片、实际切片、最终交付物(及完整路径)。

## Common Mistakes(本 skill 真实踩过)

| 坑 | 真相 / 对策 |
|---|---|
| 假设剪映草稿明文,硬写工程 | 新版剪映(10.x)**加密草稿**,明文被拒。Step 0 先验 `draft_format`。 |
| 假设 ffmpeg 有 drawtext | Homebrew 版常没编 libfreetype。用 `render_text.py`。 |
| 字体路径写死 | 不同机器字体不同。render_text 自动回退 + `detect_env` 报 `cjk_font`。 |
| 字幕凭画面瞎猜写死 | 会标错(点香≠点灯)。标"待确认"、请用户核对。 |
| 4K 软件编码慢/超时 | 用 `hwaccel=videotoolbox`;否则长段分批切。 |
| 路径写死成别人机器 | 用 `detect_env.sh` 的 `draft_root`、`command -v`。 |
| 剪映运行时改 root_meta | 被退出覆盖。顺序:退出→登记→打开。 |
| zsh:`-map 0:a?` / 数组 0 起始 | `?` 被当通配(加引号);zsh 数组**1 起始**,映射别错位。 |
| 删了分段没法二次改 | 留 `build/`、`clips/`,增量编辑几秒搞定。 |
