# -*- coding: utf-8 -*-
"""绕过 github.com（该域名在本机网络不可达），直接用 GitHub Contents API 提交文件。"""
import os, sys, json, base64, time, pathlib, urllib.request, urllib.error
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(r'C:/Users/tyq/WorkBuddy/2026-10-23-09-01-43')
OWNER, REPO = 'smilence2777', 'g2-english-media'
API = 'https://api.github.com'

token = os.environ.get('GH_TOKEN')
if not token:
    print('GH_TOKEN missing'); sys.exit(1)

SKIP_DIRS = {'.git', '.workbuddy', '__pycache__'}
SKIP_SUFFIX = {'.genie', '.pyc'}

files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for f in filenames:
        p = pathlib.Path(dirpath) / f
        if p.suffix in SKIP_SUFFIX:
            continue
        rel = p.relative_to(ROOT).as_posix()
        files.append((rel, p))
files.sort()

def put(item):
    rel, p = item
    data = p.read_bytes()
    body = json.dumps({
        'message': 'add: ' + rel,
        'content': base64.b64encode(data).decode('ascii'),
    }).encode('utf-8')
    url = '%s/repos/%s/%s/contents/%s' % (API, OWNER, REPO, quote(rel))
    req = urllib.request.Request(url, data=body, method='PUT', headers={
        'Authorization': 'token ' + token,
        'Accept': 'application/vnd.github+json',
        'Content-Type': 'application/json',
        'User-Agent': 'workbuddy-uploader',
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
                return (True, rel, d.get('content', {}).get('size', 0))
        except urllib.error.HTTPError as e:
            detail = e.read()[:200].decode('utf-8', 'ignore')
            if attempt == 2:
                return (False, rel, 'HTTP %s %s' % (e.code, detail))
            time.sleep(2 + attempt * 3)
        except Exception as e:
            if attempt == 2:
                return (False, rel, repr(e)[:200])
            time.sleep(2 + attempt * 3)
    return (False, rel, 'unknown')

print('files:', len(files), flush=True)
ok = fail = 0
t0 = time.time()
with ThreadPoolExecutor(max_workers=4) as ex:
    for good, rel, info in ex.map(put, files):
        if good:
            ok += 1
            print('OK  %3d/%d  %s' % (ok, len(files), rel), flush=True)
        else:
            fail += 1
            print('ERR        %s -> %s' % (rel, info), flush=True)
print('done ok=%d fail=%d elapsed=%.1fs' % (ok, fail, time.time() - t0))
