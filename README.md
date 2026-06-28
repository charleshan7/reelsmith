# reelsmith — CapCut / 剪映 自适应集锦剪辑 Skill

一个给 AI Agent(Claude Code / Codex / 等支持 [Agent Skills](https://agentskills.io) 的运行时)用的**视频集锦剪辑工作流 skill**:把会议录制或一堆本地素材,变成带片头标题卡和字幕的高光成片——**自动适配你的机器**,而不是写死路径和工具。

> An adaptive skill that turns meeting recordings or local clips into a highlight package (title card + subtitles), delivering either an editable CapCut/剪映 draft **or** a finished MP4 — whichever the local environment actually supports.

## 为什么是"自适应"

市面上很多剪辑 skill 把作者那台机器的路径、工具、剪映版本写死了,换一台就崩。这个 skill 的第一步永远是**探测环境**,再据此分支:

- **剪映草稿是明文** → 直接生成可在 app 里编辑的剪映工程。
- **剪映草稿是加密的**(剪映专业版 10.x 起就加密了)→ 自动降级,产出烧好字幕的 MP4 成片。
- **ffmpeg 没编 drawtext**(Homebrew 版常见)→ 改用 PIL 渲染文字再 overlay。
- **支持 VideoToolbox** → 4K/HEVC 走硬件加速,快数倍。
- **字体/草稿目录/工具** → 全部探测,带跨平台回退。

## 目录结构

```
reelsmith/
├── SKILL.md                # 主工作流(Agent 读这个)
├── scripts/
│   ├── detect_env.sh       # 环境探测:工具/字体/草稿格式/硬件加速/磁盘
│   └── render_text.py      # 文字→透明PNG(字体回退·自动换行·横竖屏),供 ffmpeg overlay
├── agents/openai.yaml      # Codex/OpenAI 运行时的元数据(可选)
├── LICENSE
└── README.md
```

## 依赖

- **必需**:`ffmpeg` / `ffprobe`、`python3` + `Pillow`(PIL)
- **可选**:`node`(生成/校验剪映工程 JSON)、`capcut-cli` / `cutCLI`(若已装可辅助)
- **平台**:主要在 macOS 验证(VideoToolbox、剪映草稿路径);脚本对 Linux 字体路径做了回退。

```bash
# macOS
brew install ffmpeg
python3 -m pip install Pillow
```

## 安装

把整个文件夹放进你运行时的 skills 目录:

```bash
# Claude Code
git clone https://github.com/charleshan7/reelsmith.git \
  ~/.claude/skills/reelsmith
# 跨运行时通用别名:~/.agents/skills/
```

## 用法

直接对 Agent 说,例如:

- “我给你一个腾讯会议录制链接,帮我剪视频集锦”
- “这几个本地视频,取精华剪成一个高光,放下载夹”
- “把这段也剪进已有的成片里”

Agent 会:探测环境 → 写剪辑方案 → 切片 → 加片头/字幕 → 按环境产出剪映工程或 MP4。

也可单独跑脚本:

```bash
bash scripts/detect_env.sh
python3 scripts/render_text.py "字幕文字" out.png --size 60 --canvas 1920x1080
```

## 已知限制

- **加密版剪映无法自动生成可编辑工程**——这是剪映自身的加密,非本 skill 缺陷;此时产出 MP4,你仍可把素材/成片导入剪映手动再编。
- 剪映工程生成路径仅在明文草稿版本上验证过。

## License

MIT — 见 [LICENSE](LICENSE)。
