import json,os,glob
from datetime import datetime
def ts(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
fs=glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))
print('total sessions',len(fs), 'GB',round(sum(map(os.path.getsize,fs))/1e9,2))
fs.sort(key=os.path.getsize,reverse=True)
for f in fs[:5]:
    n=c=u=0;a=b=None;inp=cr=cw=out=0;models=set()
    for line in open(f,'rb'):
        n+=1
        if b'compact_boundary' in line: c+=1
        try:o=json.loads(line)
        except: continue
        t=o.get('timestamp')
        if t:
            a=a or t;b=t
        if o.get('type')=='user' and isinstance(o.get('message',{}).get('content'),str): u+=1
        m=o.get('message') or {}
        if o.get('type')=='assistant' and isinstance(m,dict):
            us=m.get('usage') or {}; models.add(m.get('model'))
            inp+=us.get('input_tokens',0);cr+=us.get('cache_read_input_tokens',0);cw+=us.get('cache_creation_input_tokens',0);out+=us.get('output_tokens',0)
    tot=inp+cr+cw
    print(f"{os.path.getsize(f)/1e6:.0f}MB lines={n} {a}->{b} dur={(ts(b)-ts(a)) if a else None} compact={c} user_text_msgs={u} cache_read%={100*cr/tot if tot else 0:.1f} out={out} models={models} {f.split('projects/')[1][:90]}")
