# -*- coding: utf-8 -*-
"""扫描 media 目录，生成单文件音视频播放器 index.html"""
import os, json, re, pathlib

ROOT = pathlib.Path(r'C:/Users/tyq/WorkBuddy/2026-10-23-09-01-43')
BASE = ROOT / '新交际二上音视频'
AUDIO_DIR = BASE / '课文和单词音频'
VIDEO_DIR = BASE / '课文动画视频'

AUDIO_EXT = {'.mp3', '.m4a', '.wav', '.aac'}
VIDEO_EXT = {'.mp4', '.webm', '.mov', '.mkv'}


def nice(name: str) -> str:
    """把原始文件名整理成好看的显示名"""
    s = os.path.splitext(name)[0]
    s = s.replace('‘', "'").replace('’', "'")
    s = re.sub(r'\bacit+vity\b', 'Activity', s, flags=re.I)
    s = re.sub(r'\bactivity\b', 'Activity', s, flags=re.I)
    s = re.sub(r"\blet's explore\b", "Let's explore", s, flags=re.I)
    s = re.sub(r'\bUnit\s*(\d+)\b', r'Unit \1', s, flags=re.I)
    return s.strip()


UNIT_RE = re.compile(r'unit\s*(\d+)', re.I)


def group_of(disp: str, fname: str) -> str:
    m = UNIT_RE.search(disp)
    if m:
        return 'Unit %d' % int(m.group(1))
    return '附录 / 其他'


def scan(directory, exts):
    items = []
    if not directory.exists():
        return items
    for f in sorted(os.listdir(directory)):
        p = directory / f
        if p.is_file() and p.suffix.lower() in exts:
            rel = p.relative_to(ROOT).as_posix()
            disp = nice(f)
            items.append({
                'name': disp,
                'file': f,
                'path': rel,
                'g': group_of(disp, f),
            })
    items.sort(key=lambda x: (x['g'], x['name']))
    return items


audio = scan(AUDIO_DIR, AUDIO_EXT)
video = scan(VIDEO_DIR, VIDEO_EXT)

# 单元内排序：课文在前、单词在后（音频）；activity 1/2 → let's explore（视频）
def audio_sort_key_within_group(it):
    n = it['name']
    if '单词' in n:
        return (1, n)
    return (0, n)


for g in {i['g'] for i in audio}:
    pass

data = {
    'audio': audio,
    'video': video,
}

TPL = ROOT / 'template.html'
html = TPL.read_text(encoding='utf-8')
html = html.replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False, indent=1))
out = ROOT / 'index.html'
out.write_text(html, encoding='utf-8')
print('audio:', len(audio), 'video:', len(video))
print('written:', out, out.stat().st_size, 'bytes')
