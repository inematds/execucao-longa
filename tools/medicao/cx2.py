import json,os,glob,collections
from datetime import datetime
def ts(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
rows=[]
for f in glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True):
    sz=os.path.getsize(f)
    with open(f,'rb') as fh:
        try: a=json.loads(fh.readline())['timestamp']
        except: continue
        fh.seek(max(0,sz-2_000_000)); tail=fh.read().splitlines()
    b=None
    for l in reversed(tail):
        try: b=json.loads(l)['timestamp'];break
        except: pass
    if b: rows.append(((ts(b)-ts(a)).total_seconds()/86400,sz,f))
rows.sort(reverse=True)
for d,sz,f in rows[:8]: print(f"{d:.2f}d {sz/1e6:.0f}MB {f.split('sessions/')[1]}")
print('>=1.2GB:',[ (round(s/1e9,2),f.split('sessions/')[1]) for d,s,f in rows if s>1.2e9])
# biggest: size by record type
f=max(rows,key=lambda r:r[1])[2]
sizes=collections.Counter();urole=collections.Counter();big=[]
with open(f,'rb') as fh:
  for line in fh:
    o=json.loads(line);p=o.get('payload') or {}
    k=(o.get('type'),p.get('type') if isinstance(p,dict) else None);sizes[k]+=len(line)
    if isinstance(p,dict) and p.get('type')=='message': urole[p.get('role')]+=1
print('bytes by type',[(k,round(v/1e6)) for k,v in sizes.most_common(8)])
print('message roles',urole)
