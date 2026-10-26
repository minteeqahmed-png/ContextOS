"""Explicit live Gemini acceptance test with only authored public demo fixtures.

Uses real OCR, API review/approval, vision workers, persistence and search.
Automated approval here is limited to the fixtures generated in this script.
Never opens or sends the user's personal capture library.
"""
import base64
from datetime import datetime
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / '.runtime')]
from start_gemini import configure
configure()
import os
OUT = ROOT / 'evaluation' / 'output' / 'full-demo'
OUT.mkdir(parents=True, exist_ok=True)
os.environ['CONTEXTOS_DB'] = str(OUT / ('run-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3'))
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
import backend as b

# Record only this script's generated-fixture responses for debugging actual inference.
real_infer = b.vp.infer
def recorded_infer(body, target):
    result = real_infer(body, target)
    (OUT / ('response-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result
b.vp.infer = recorded_infer


def fixtures():
    for name in ('dip', 'rise', 'layout'):
        im = Image.new('RGB', (800, 500), 'white')
        d = ImageDraw.Draw(im)
        d.text((30, 15), 'PUBLIC SYNTHETIC DEMO', fill='black', font_size=20)
        if name != 'layout':
            d.line([(70, 60), (70, 430), (740, 430)], fill='black', width=3)
            points = [(90,180),(210,190),(330,330),(420,360),(540,190),(660,70),(720,90)] if name=='dip' else [(90,370),(210,310),(330,260),(420,210),(540,160),(660,100),(720,60)]
            d.line(points, fill='#008830', width=8)
            d.ellipse((650,320,700,370), fill='#dc2020' if name=='dip' else '#2050dc')
        else:
            d.rectangle((30,60,380,460), fill='#101820')
            d.text((55,90), '> npm run dev', fill='#66ff99', font_size=24)
            d.rectangle((410,60,770,460), fill='#eeeeee', outline='#777777', width=3)
            d.rectangle((410,60,770,95), fill='#cccccc')
            d.rectangle((440,135,740,200), fill='#4477cc')
            for x in (445,550,655): d.rectangle((x,235,x+80,360), fill='white', outline='#888888')
        path = ROOT / 'evaluation' / 'sources' / ('visual-'+name+'.png')
        path.parent.mkdir(parents=True, exist_ok=True);im.save(path)
        yield name, 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()


def main():
    report = {'model': os.environ['CONTEXTOS_VISION_MODEL'], 'dataset': '3 generated image imports; not real browser captures; no private data', 'captures': [], 'queries': []}
    def save(): (OUT/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    mapping = {}
    with TestClient(b.app) as client:
        for i, (name, image) in enumerate(fixtures()):
            t = time.perf_counter()
            r = client.post('/api/memories', json={'title':'Demo frame '+str(i+1), 'image':image, 'session':'Visual demo', 'source_kind':'browser', 'type':'Browser', 'source_url':'http://127.0.0.1:8003/demo/visual-'+name+'.png'})
            r.raise_for_status();key=r.json()['id'];mapping[key]=name
            ack = (time.perf_counter()-t)*1000
            b.jobs[(str(b.DB_PATH),key)].result(timeout=240)
            p=client.post('/api/memories/'+key+'/privacy/prepare',json={'masks':[]});p.raise_for_status();p=p.json()
            assert p['target']['model']==report['model']
            # Only the generated fixture is approved, through the production digest endpoint.
            r=client.post('/api/memories/'+key+'/privacy/approve',json={'digest':p['digest']});r.raise_for_status()
            b.vision_jobs[(str(b.DB_PATH),key)].result(timeout=180)
            m=client.get('/api/memories/'+key).json()
            report['captures'].append({'fixture':name,'id':key,'http_ack_ms':round(ack,2),'telemetry':m['telemetry'],'stages':m['stages'],'ocr_text':m['ocr_text'],'description':m.get('visual_description',''),'issues':m['issues']})
            assert client.get('/demo/visual-'+name+'.png').status_code==200
            save();print('Processed',name,m['stages'],flush=True)
        for query, expected in [('green line dips then rises steeply',['dip']),('green line steadily increases',['rise']),('dark terminal left browser preview right',['layout']),('green chart',['dip','rise']),('purple elephant submarine',[])]:
            t=time.perf_counter();r=client.get('/api/search',params={'q':query,'library':'captures','tz':'Asia/Karachi','session':'Visual demo'});r.raise_for_status();result=r.json()
            names=[mapping[k] for k in result['ids']]
            report['queries'].append({'query':query,'expected':expected,'retrieved':names,'top1':bool(names and names[0] in expected) if expected else not names,'top3':bool(set(names[:3])&set(expected)) if expected else not names,'ms':round((time.perf_counter()-t)*1000,2),'mode':result['mode']})
        key=next(k for k,v in mapping.items() if v=='dip')
        p=client.post('/api/memories/'+key+'/grounding/prepare',json={'query':'Where is the red circular indicator relative to the high point of the green line? Cite both regions.'});p.raise_for_status();p=p.json()
        r=client.post('/api/grounding/'+p['id']+'/approve',json={'digest':p['digest']})
        report['grounding_http_status']=r.status_code
        report['grounding']={k:v for k,v in r.json().items() if k!='image'}
        with b.database() as db:
            report['persisted_captures']=len([x for x in db.execute('SELECT id FROM memories') if x['id'] in mapping])
        key=next(k for k,v in mapping.items() if v=='rise')
        client.delete('/api/memories/'+key).raise_for_status()
        with b.database() as db:
            report['deletion_verified']=all(db.execute('SELECT count(*) FROM '+table+' WHERE '+col+'=?',(key,)).fetchone()[0]==0 for table,col in [('memories','id'),('recall','id'),('privacy','id'),('work','id'),('grounding','memory_id')])
        positive=[q for q in report['queries'] if q['expected']]
        report['metrics']={'top1':sum(q['top1'] for q in positive)/len(positive),'top3':sum(q['top3'] for q in positive)/len(positive),'positive_queries':len(positive),'median_search_ms':statistics.median(q['ms'] for q in report['queries'])}
        save();print(json.dumps(report['metrics']),flush=True)


if __name__=='__main__': main()
