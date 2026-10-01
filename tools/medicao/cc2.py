import os,glob,re
from datetime import datetime
R=re.compile(rb'"timestamp":"([^"]+)"')
fs=[f for f in glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl')) if 'observer' not in f]
rows=[]
for f in fs:
    d=open(f,'rb').read()
    c=d.count(b'"subtype":"compact_boundary"')
    t=R.findall(d)
    if not t: continue
    a=datetime.fromisoformat(t[0].decode().replace('Z','+00:00'));b=datetime.fromisoformat(t[-1].decode().replace('Z','+00:00'))
    rows.append((c,(b-a).total_seconds()/3600,len(d),f))
print('sessions with >=1 compact:',sum(1 for r in rows if r[0]>0),'of',len(rows))
for r in sorted(rows,reverse=True)[:5]: print(f"compact={r[0]} {r[1]:.1f}h {r[2]/1e6:.0f}MB {r[3].split('projects/')[1][:80]}")
print('-- longest')
for r in sorted(rows,key=lambda r:r[1],reverse=True)[:5]: print(f"{r[1]/24:.1f}d compact={r[0]} {r[2]/1e6:.0f}MB {r[3].split('projects/')[1][:80]}")
