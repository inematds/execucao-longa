import json,sys,os,glob,collections
from datetime import datetime
def ts(s):
    try: return datetime.fromisoformat(s.replace('Z','+00:00'))
    except: return None
files=sorted(glob.glob(os.path.expanduser('~/.codex/sessions/**/*.jsonl'),recursive=True),key=os.path.getsize,reverse=True)[:10]
for i,f in enumerate(files):
    n=0;first=last=None;types=collections.Counter();pt=collections.Counter();tok=None;usr=0;tc=0;model=set();compact=0
    with open(f,'rb') as fh:
        for line in fh:
            n+=1
            try:o=json.loads(line)
            except: continue
            t=o.get('timestamp')
            if t:
                if first is None:first=t
                last=t
            ty=o.get('type');types[ty]+=1
            p=o.get('payload') or {}
            if isinstance(p,dict):
                st=p.get('type');pt[(ty,st)]+=1
                if ty=='turn_context':
                    tc+=1; m=p.get('model'); 
                    if m:model.add(m)
                if st=='token_count' and p.get('info'):
                    tok=p['info']
                if st=='user_message':usr+=1
            if ty=='compacted' or 'compact' in str(ty):compact+=1
    a,b=ts(first),ts(last)
    dur=(b-a) if a and b else None
    print(f"#{i} {os.path.getsize(f)/1e9:.2f}GB lines={n} first={first} last={last} dur={dur} turn_ctx={tc} user_msgs={usr} compacted={compact} models={model}")
    if i==0:
        print(' types',types.most_common(12))
        print(' ptypes',[ (k,v) for k,v in pt.most_common(25)])
        if tok:
            print(' total_usage',json.dumps(tok.get('total_token_usage')), 'ctxwin',tok.get('model_context_window'))
