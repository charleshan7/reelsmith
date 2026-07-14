# AGENTS.md — reelsmith 开发指南

给接手本项目的 AI 编程助手的说明。**运行时的完整流程说明在 SKILL.md**（它就是给 agent 读的主文档），本文件只补充开发/维护视角的背景。

## 项目一句话

自适应视频高光剪辑 Skill：从原始素材（会议录制、航拍、随手拍）自动挑高光片段，加标题卡和字幕，ffmpeg 渲染出成片 MP4。开源于 github.com/charleshan7/reelsmith。

## 设计哲学（改代码前先理解）

1. **自适应，不写死环境**：一切从 `scripts/detect_env.sh` 开始——探测 ffmpeg 能力、可用字体、硬件加速，后续步骤按探测结果分支。给它加功能时延续这个模式，不要假设任何工具/字体/路径存在。
2. **纯 MP4 输出，不生成剪映工程**：新版剪映（专业版 10.x）草稿是加密格式，明文工程会被拒（"格式不支持/无权限"），绕过需要私钥、做不到。历史上尝试过并已放弃，相关代码已删。成片让用户手动导入任何剪辑器。
3. **文字渲染走 PIL → PNG → ffmpeg overlay**，不是 drawtext：因为很多机器（如 Homebrew ffmpeg）没编 libfreetype/libass。`scripts/render_text.py` 负责渲染。中文字体探测优先系统字体（如 Arial Unicode）。
4. **`edit-plan.json` 是执行的单一事实源**（借鉴 OpenCut 的可序列化时间线）：切片命令、concat 列表、验收清单全从 json 派生，`edit-plan.md` 只给人确认。切点一律帧对齐（帧号定刀，秒 = 帧/30），切片自带 30ms 音频淡变防拼接爆音。将来 OpenCut 重写版的 headless/Editor API 落地后，这份 json 可映射成其工程格式，补上第 2 条"不生成剪辑工程文件"的缺口。

## 与姊妹工具的分工

- **无人声素材**（航拍/风景/纯画面）→ reelsmith（看画面挑高光，不转录、零 API 费用）
- **有人声素材**（口播/教程/访谈）→ 用 video-use（browser-use 开源，ElevenLabs 逐词转录驱动精剪）。不要往 reelsmith 里加转录功能，分工已定。

## 用户成片偏好（历史确认过的默认值）

标题和字幕都用**白色字、放画面底部**（字幕样式），白字配深色描边保证可读。不要蓝色字、不要大色块标题条。

## 溯源

前身是他人的 `capcut-video-highlights`（写死路径 + 假设明文剪映草稿），本项目是重写的自适应版。署名 feifeidouya。
