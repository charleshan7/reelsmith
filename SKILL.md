---
name: reelsmith
description: Use when turning a meeting recording or local video clips (腾讯会议/飞书录制、DJI/手机/相机素材) into a highlight video — auto-selecting the good parts, adding a title card and subtitles, and rendering a finished MP4. Also use to insert or append extra highlights into an already-rendered cut, or to add background music. Adapts to the local environment instead of assuming fixed paths, tools, or fonts. The finished MP4 (and the cut clips) can be manually imported into any editor afterward.
---

# reelsmith — 视频集锦自动剪辑(自适应)

## 核心原则

把会议录制或一堆本地素材,自动剪成**带片头标题和字幕的精华短片(MP4)**。成片可直接发布,也能**手动导入剪映或任何剪辑软件**继续加工。

**先探测环境,再开工。** 不要假设工具、路径、字体——这些因机器而异,写死必崩。

## Step 0 — 环境探测(必做,第一步)

```bash
bash scripts/detect_env.sh
```

| 字段 | 据此做什么 |
|---|---|
| `ffmpeg_drawtext=no` | ffmpeg 没编 libfreetype(Homebrew 常见)→ 用 `scripts/render_text.py`(PIL)渲染文字 PNG,再 ffmpeg `overlay` |
| `hwaccel=videotoolbox` | 4K/HEVC 用硬件加速,**快数倍**(见 Step 3) |
| `cjk_font` | 传给 render_text 的 `--font`(脚本本身也会自动回退) |
| `tool_*` / `disk_free` | 可用工具 / 磁盘余量(4K 工程很占地) |

**把探测结果 + 将出横屏还是竖屏,告诉用户再动手。**

## 工作流

### 1. 接入素材 + 建工作目录

输入:腾讯会议/飞书链接,或本地视频路径。建工作目录(用户指定则用之,否则 `~/Documents/video-edits/<项目名>/`):

```text
<workdir>/  source/  clips/  checks/  build/  assets/  edit-plan.md  edit-plan.json  notes.md
```

飞书录制优先用 lark-minutes / lark-vc 取转写、纪要、媒体;腾讯会议用浏览器/授权下载。**链接受阻就说清卡在哪,用已有本地素材继续。**

### 2. 写 `edit-plan.md` + `edit-plan.json`(动刀前必做)

带**具体时间区间**的方案,不能是空泛大纲。无转写时(航拍/空镜)**先抽帧看画面**再定:

```bash
ffmpeg -nostdin -v error -ss "$t" -i "$src" -frames:v 1 -vf scale=480:-1 "checks/thumbs/<id>_<pct>.jpg"
```

方案含:每切片的 源/In/Out/时长/内容/**字幕文案**/输出名,以及**画幅(横屏 1920×1080 或竖屏 1080×1920)**、标题、字幕风格。

**In/Out 一律帧对齐**:先定帧号(`frame = round(秒 × 30)`),秒数用 `帧号/30` 反推,ffmpeg 参数、concat 时长全部由帧号派生。任意小数秒下刀会被量化到最近帧——plan 与成片差 ±1 帧、抽帧验收误判、多段时长累计漂移。

`edit-plan.md` 给用户确认;确认后落一份机器可读的 `edit-plan.json` 作为**执行的单一事实源**——切片命令、concat.txt、验收清单都从它生成,增量编辑改 json 重跑,改前先备份(即天然 undo):

```json
{ "canvas": "1920x1080", "fps": 30,
  "segments": [
    { "id": "seg01", "source": "source/a.mp4", "in_frame": 4230, "out_frame": 4590,
      "subtitle": "满院许愿祈福", "output": "build/seg01.mp4" } ] }
```

> **字幕文案是"看图推断"的,不是事实。** 涉及仪式、地名、专有动作(如祈福/上香/点香)时,在 plan 里标注"待确认"并**请用户核对**——别把推断当真写死(实测教训:曾把"点香"误标成"点灯")。

### 3. ffmpeg 切片

先 `ffprobe` 量时长/规格(别猜)。切片(高光重编码精切;4K 源建议降 1080p):

```bash
# in/out 秒数由 edit-plan.json 的帧号派生;fade_st = 段时长 − 0.03:
in=$(awk -v f="$in_frame" 'BEGIN{printf "%.3f", f/30}')
out=$(awk -v f="$out_frame" 'BEGIN{printf "%.3f", f/30}')
fade_st=$(awk -v i="$in" -v o="$out" 'BEGIN{printf "%.3f", o-i-0.03}')
# hwaccel=videotoolbox 时,加 -hwaccel videotoolbox 解码、用 *_videotoolbox 编码,快数倍:
ffmpeg -nostdin -v error -y -hwaccel videotoolbox -ss "$in" -to "$out" -i "$src" \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" \
  -af "afade=t=in:d=0.03,afade=t=out:st=$fade_st:d=0.03" \
  -r 30 -c:v h264_videotoolbox -b:v 10M -pix_fmt yuv420p \
  -c:a aac -ar 48000 -ac 2 -b:a 160k "clips/$name"
# 无硬件加速时回退:-c:v libx264 -preset veryfast -crf 20 (更慢;4K 长段分批切防超时)
```
竖屏 9:16 把 `scale/crop` 改成 `1080:1920`。切完用 `ffprobe` 核对时长。**30ms afade 必加**:各段独立编码 AAC 再 concat,切点没有淡入淡出会有爆音/click。

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

封面同理:freeze + 文字 → 可作为成片缩略图。

### 5. 合成 MP4 成片

标题卡 + 各带字幕段,统一参数(横屏 1920×1080 或竖屏 1080×1920 / 30fps / h264 yuv420p / aac 48k stereo)后拼接。标题卡补静音音轨(`anullsrc`)才能与有声段 concat:

```bash
ffmpeg -nostdin -v error -y -i clips/clip00_title.mp4 -i assets/title.png \
  -f lavfi -t 1 -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -filter_complex "[0:v][1:v]overlay=0:0,fps=30,format=yuv420p[v]" \
  -map "[v]" -map 2:a -shortest \
  -c:v libx264 -preset veryfast -crf 20 -c:a aac -ar 48000 -ac 2 -b:a 160k build/seg00.mp4
# concat 顺序从 edit-plan.json 的 segments 生成,别手敲
printf "file 'seg00.mp4'\nfile 'seg01.mp4'\n..." > build/concat.txt
ffmpeg -nostdin -v error -y -f concat -safe 0 -i build/concat.txt -c copy "成片.mp4"
```

抽帧验收(标题卡 + 每条字幕),逐条确认:**字幕文字与画面内容相符**、无错位、时长符合 plan。

> 成片是 MP4。用户若想精修,可把它(或 `clips/` 里切好的片段)**手动拖进剪映 / CapCut / Premiere 等任意剪辑软件**再加工——本 skill 不直接生成剪辑工程文件。

### 6. 增量编辑:把素材插进/接到已有成片

**切完别删 `build/` 分段和 `clips/`** —— 二次编辑全靠它们,几秒就能改:

1. 按 Step 3/4 把新素材切片(帧对齐 + 30ms afade)、叠字幕,生成新段 `build/seg_x.mp4`(同参数)。
2. 备份 `edit-plan.json` 后把新段插到目标位置(开头/中间/结尾),由 json 重新生成 concat 列表。
3. `-c copy` 重拼即可,无需重渲染旧段。
4. 覆盖输出前**备份旧成片**;抽帧验收插入点。

> 同参数(分辨率/帧率/编码/音频采样率)是 `-c copy` 无缝拼接的前提;不一致会拼接失败或卡顿,需重编码统一。

## 可选:背景音乐 / 杂音处理

原声嘈杂(风声/人群)时,加 BGM 并压低或静音环境声:

```bash
# 静音原声、只用 BGM:
ffmpeg -y -i 成片.mp4 -i bgm.mp3 -map 0:v -map 1:a -shortest -c:v copy -c:a aac out.mp4
# 保留环境声但压低、与 BGM 混音(BGM 0.8 / 原声 0.25):
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
- 切片前必有 `edit-plan.md` + `edit-plan.json`;**In/Out 帧对齐,秒数由帧号派生**;时长用 `ffprobe` 实测;路径/工具/字体**一律用探测值,绝不写死别人机器的路径**。
- **字幕推断需用户核对**,仪式/专有动作尤其要确认。
- 覆盖任何已有成片前先备份;留 `build/`、`clips/` 供二次编辑。
- 源不可访问就如实说,用现有素材继续,不凭空编造切片。
- 最终回复清楚区分:源素材、计划切片、实际切片、最终成片(及完整路径)。

## Common Mistakes(本 skill 真实踩过)

| 坑 | 真相 / 对策 |
|---|---|
| 假设 ffmpeg 有 drawtext | Homebrew 版常没编 libfreetype。用 `render_text.py`。 |
| 字体路径写死 | 不同机器字体不同。render_text 自动回退 + `detect_env` 报 `cjk_font`。 |
| 字幕凭画面瞎猜写死 | 会标错(点香≠点灯)。标"待确认"、请用户核对。 |
| 4K 软件编码慢/超时 | 用 `hwaccel=videotoolbox`;否则长段分批切。 |
| 路径写死成别人机器 | 用 `command -v` 找工具,工作目录用探测/约定路径。 |
| zsh:`-map 0:a?` / 数组 0 起始 | `?` 被当通配(加引号);zsh 数组**1 起始**,映射别错位。 |
| 删了分段没法二次改 | 留 `build/`、`clips/`,增量编辑几秒搞定。 |
| 任意小数秒下刀 | 切点被量化到最近帧:plan 与成片差 ±1 帧、多段时长累计漂移。帧号定切点,秒 = 帧/30。 |
| 分段 AAC 拼接切点爆音 | 切片时每段加 30ms `afade` 淡入淡出(Step 3),拼接处即无 click。 |
