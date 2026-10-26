"""Deterministic temporal constraints and evidence-based local ranking."""
import math
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

STOP = set('the i a an was saw what that from had in my for of to it during open looking me show is were how much cost costs remember with and on at this s plan table page pdf browser website document screenshot'.split())
STOP.update('did capture captured saved find get see please snapshot snapshots memories memory'.split())
DAYS = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']


def terms(text):
    return [t for t in re.findall(r'\w+', text.lower()) if t not in STOP and len(t)>1]


def constraints(query, timezone, items, now=None):
    zone = ZoneInfo(timezone)
    today = (now or datetime.now(zone)).astimezone(zone).date()
    text = query.lower()
    start = end = None
    labels = []
    iso = re.search(r'\b\d{4}-\d{2}-\d{2}\b', text)
    if iso:
        start = datetime.strptime(iso[0], '%Y-%m-%d').date()
        text = text.replace(iso[0], '')
    elif 'yesterday' in text:
        start = today - timedelta(days=1)
        text = text.replace('yesterday', '')
    elif 'today' in text:
        start = today
        text = text.replace('today', '')
    elif re.search(r'\b(last|past) (week|7 days)\b', text):
        start, end = today - timedelta(days=6), today + timedelta(days=1)
        text = re.sub(r'\b(last|past) (week|7 days)\b', '', text)
    else:
        for day in DAYS:
            if re.search(r'\b'+day+r'\b', text):
                delta = (today.weekday()-DAYS.index(day)) % 7
                if delta == 0 and 'last '+day in text:
                    delta = 7
                start = today-timedelta(days=delta)
                text = re.sub(r'\b(?:last )?'+day+r'\b', '', text)
                break
    if start:
        end = end or start + timedelta(days=1)
        labels.append(f'{start.isoformat()} to {(end-timedelta(days=1)).isoformat()} · {timezone}')
    source = 'pdf' if re.search(r'\bpdf\b', text) else 'browser' if re.search(r'\b(browser|website)\b', text) else None
    if source:
        labels.append('Source: '+source)
    sessions = {m.get('session','') for m in items if m.get('session')}
    matched = [s for s in sessions if all(t in terms(text) for t in terms(s)) and terms(s)]
    session = max(matched, key=len) if matched else None
    if session:
        labels.append('Session: '+session)
        for t in terms(session):
            text = re.sub(r'\b'+re.escape(t)+r'\b', '', text)
    return {'start':start,'end':end,'zone':zone,'source':source,'session':session,'labels':labels,'terms':terms(text)}


def eligible(item, filters):
    if filters['source']=='pdf' and not (item.get('source_kind')=='pdf' or '.pdf' in item.get('origin','').lower()):
        return False
    if filters['source']=='browser' and item.get('type')!='Browser':
        return False
    if filters['session'] and item.get('session')!=filters['session']:
        return False
    if filters['start']:
        try:
            date = datetime.fromisoformat(item['date'].replace('Z','+00:00')).astimezone(filters['zone']).date()
            if not filters['start'] <= date < filters['end']:
                return False
        except (ValueError, KeyError):
            return False
    return True


def cosine(a,b):
    if not a or not b or len(a)!=len(b):
        return 0
    denominator=math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
    return sum(x*y for x,y in zip(a,b))/denominator if denominator else 0


def matches(text, tokens):
    words=set(re.findall(r'\w+',text.lower()))
    # OCR sometimes joins adjacent words. Match longer query fragments without
    # rewriting the original evidence or claiming a corrected transcription.
    return [t for t in tokens if t in words or (len(t)>=4 and any(t in word for word in words)) or (t in ('price','pricing') and words.intersection({'price','prices','pricing'}))]


def rank(items, filters, lexical_ids, vectors, query_vector):
    tokens=filters['terms']
    lexical_rank={key:i for i,key in enumerate(lexical_ids)}
    semantic=[]
    for m in items:
        score=max([cosine(query_vector,v) for v in vectors.get(m['id'],[])] or [0])
        if score >= .45:
            semantic.append((m['id'],score))
    semantic_rank={key:i for i,(key,_) in enumerate(sorted(semantic,key=lambda x:-x[1]))}
    output=[]
    for m in items:
        text=' '.join(str(m.get(k,'')) for k in ('title','text','ocr_text','visual_description','origin','session'))
        hits=matches(text,tokens)
        region_hits=sorted([(len(matches(r['text'],tokens)),r) for r in m.get('regions',[])],key=lambda p:-p[0])
        chosen=[r for n,r in region_hits if n][:5]
        # Preserve adjacent cells on the same visual row (e.g. Pro and $49).
        anchors=list(chosen)
        for r in m.get('regions',[]):
            if r in chosen:continue
            y=(r['box'][1]+r['box'][3])/2
            if any(abs(y-(a['box'][1]+a['box'][3])/2)<max(r['box'][3]-r['box'][1],a['box'][3]-a['box'][1])*.5 for a in anchors):
                chosen.append(r)
        chosen=chosen[:15]
        visual_chosen=[r for r in m.get('visual_regions',[]) if matches(r['text'],tokens)][:5]
        sem=m['id'] in semantic_rank
        if tokens and not hits and not sem:
            continue
        if len(tokens)>2 and len(hits)<2 and not sem:
            continue
        strength='Evidence match' if hits and len(hits)>=max(1,len(tokens)*.5) else 'Possible match' if tokens else 'Context match'
        reasons=[]
        if hits:
            literal=' '.join(str(m.get(k,'')) for k in ('title','text','ocr_text','origin','session'))
            literal_hits=matches(literal,tokens)
            reasons.append(('Text contains ' if literal_hits else 'Model visual description contains ')+', '.join(dict.fromkeys(hits)))
            if not literal_hits:strength='Possible visual match'
        if sem:
            reasons.append('Related by local embeddings')
        reasons.extend(filters['labels'])
        score=len(hits)/max(1,len(tokens)) + (min(3,region_hits[0][0])*.05 if region_hits else 0)
        score+=1/(60+lexical_rank[m['id']]) if m['id'] in lexical_rank else 0
        score+=1/(60+semantic_rank[m['id']]) if sem else 0
        output.append({'id':m['id'],'score':score,'label':strength,'reason':'; '.join(reasons) or 'Matches the selected library','region_ids':[r['id'] for r in chosen+visual_chosen], 'quotes':[r['text'] for r in chosen], 'visual_interpretations':[r['text'] for r in visual_chosen]})
    output.sort(key=lambda x:-x['score'])
    return [{k:v for k,v in row.items() if k!='score'} for row in output]
