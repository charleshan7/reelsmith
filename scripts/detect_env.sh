#!/usr/bin/env bash
# Probe the local video-editing environment. Prints KEY=VALUE so the skill can
# decide between delivering a CapCut/剪映 draft vs a finished MP4, and pick the
# fastest, most compatible commands. Run: bash detect_env.sh
set -u

say(){ printf '%s=%s\n' "$1" "$2"; }

# --- tools ---
for t in ffmpeg ffprobe node python3 capcut cutCLI; do
  p=$(command -v "$t" 2>/dev/null) && say "tool_$t" "$p" || say "tool_$t" "MISSING"
done

# --- ffmpeg text capability (drawtext/subtitles need libfreetype/libass) ---
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' drawtext ' \
    && say "ffmpeg_drawtext" "yes" || say "ffmpeg_drawtext" "no"  # no -> use render_text.py (PIL)
  # hardware accel (macOS VideoToolbox) -> big speedup on 4K HEVC
  if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q 'h264_videotoolbox'; then
    say "hwaccel" "videotoolbox"   # encode: -c:v h264_videotoolbox ; decode: -hwaccel videotoolbox
  else
    say "hwaccel" "none"
  fi
fi

# --- Python PIL (text rendering fallback) ---
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import PIL" 2>/dev/null && say "python_pil" "yes" || say "python_pil" "no"
fi

# --- CJK-capable font for render_text.py ---
FONT="MISSING"
for f in \
  "/System/Library/Fonts/PingFang.ttc" \
  "/System/Library/Fonts/Supplemental/Arial Unicode.ttf" \
  "/System/Library/Fonts/STHeiti Medium.ttc" \
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" \
  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; do
  [ -f "$f" ] && FONT="$f" && break
done
say "cjk_font" "$FONT"

# --- CapCut / 剪映 draft root ---
DRAFT_ROOT=""
for d in \
  "$HOME/Movies/JianyingPro/User Data/Projects/com.lveditor.draft" \
  "$HOME/Movies/CapCut/User Data/Projects/com.lveditor.draft"; do
  [ -d "$d" ] && DRAFT_ROOT="$d" && break
done
say "draft_root" "${DRAFT_ROOT:-MISSING}"

# --- KEY: is the draft format encrypted? (decides if a draft can be hand-authored) ---
# Peek at any existing draft_info.json: '{' first byte == plaintext, else encrypted.
ENC="unknown"
if [ -n "$DRAFT_ROOT" ]; then
  SAMPLE=$(find "$DRAFT_ROOT" -maxdepth 2 -name draft_info.json 2>/dev/null | head -1)
  if [ -n "$SAMPLE" ]; then
    [ "$(head -c1 "$SAMPLE" 2>/dev/null)" = "{" ] && ENC="plaintext" || ENC="encrypted"
  fi
fi
say "draft_format" "$ENC"   # plaintext=can author draft / encrypted=MP4 only / unknown=no sample

# --- free disk space on home volume (4K projects are large) ---
say "disk_free" "$(df -h "$HOME" 2>/dev/null | awk 'NR==2{print $4}')"

# --- recommendation ---
[ "$ENC" = "plaintext" ] && say "recommend_output" "jianying_draft" || say "recommend_output" "mp4"
