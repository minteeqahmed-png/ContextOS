"""Evaluate actual browser screenshots and a PDF in an isolated local database."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.runtime'))
import base64
import json
import platform
import socket
import statistics
import tempfile
import time
from unittest.mock import patch
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import psutil
from fastapi.testclient import TestClient
import server

OUT=ROOT/'evaluation'/'output';OUT.mkdir(parents=True,exist_ok=True)
sources=[('pricing','Product meeting'),('growth','Growth review'),('code','Engineering'),('other-pricing','Vendor review')]
for name,_ in sources:
    if not (ROOT/'evaluation'/'captures'/f'{name}.png').exists():
        raise SystemExit('Missing real browser capture: '+name+'.png')
today=datetime.now(ZoneInfo('Asia/Karachi')).date()
tuesday=today-timedelta(days=(today.weekday()-1)%7)
date=tuesday.isoformat()+'T10:00:00+05:00'
queries=[
    ('What was the Pro plan price in the PDF from Tuesday’s product meeting?',['pdf']),
    ('weekly active users growth',['growth']),
    ('React debounce hook',['code']),
    ('storage version history',['other-pricing']),
    ('advanced analytics priority support',['pricing','pdf']),
    ('Pro price',['pricing','other-pricing','pdf']),
    ('PDF on '+tuesday.isoformat(),['pdf']),
    ('submarine unicorn',[]),
    ('PDF on 2001-01-01',[]),
    ('clearTimeout timer',['code']),
]
attempts=[]
real_connect=socket.socket.connect
def guarded_connect(sock,address):
    if isinstance(address,tuple) and address[0] not in ('127.0.0.1','localhost','::1'):
        attempts.append(str(address));raise RuntimeError('Non-loopback networking blocked during evaluation')
    return real_connect(sock,address)

with tempfile.TemporaryDirectory() as tmp, patch.object(socket.socket,'connect',guarded_connect):
    server.DB_PATH=Path(tmp)/'evaluation.sqlite3'
    with TestClient(server.app) as client:
        status=client.get('/api/status').json()
        mapping={};processing=[]
        for name,session in sources:
            start=time.perf_counter()
            data='data:image/png;base64,'+base64.b64encode((ROOT/'evaluation'/'captures'/f'{name}.png').read_bytes()).decode()
            response=client.post('/api/memories',json={'id':'eval-'+name,'title':'Browser capture '+name,'image':data,'type':'Browser','source_kind':'browser','source_url':f'http://127.0.0.1:8000/demo/{name}.html','session':session,'date':date})
            response.raise_for_status();key=response.json()['id'];mapping[key]=name
            server.jobs[(str(server.DB_PATH),key)].result(timeout=180)
            m=client.get('/api/memories/'+key).json()
            processing.append({'source':name,'ms':round((time.perf_counter()-start)*1000,2),'status':m['status'],'region_count':len(m['regions']),'stages':m['stages'],'issues':m['issues']})
            (OUT/(name+'-ocr.json')).write_text(json.dumps({'text':m['ocr_text'],'regions':m['regions']},indent=2),encoding='utf-8')
        start=time.perf_counter()
        response=client.post('/api/import/pdf',json={'data':base64.b64encode((ROOT/'evaluation'/'sources'/'pricing.pdf').read_bytes()).decode(),'filename':'pricing.pdf','session':'Product meeting'})
        response.raise_for_status();key=response.json()['id'];mapping[key]='pdf'
        server.jobs[(str(server.DB_PATH),key)].result(timeout=180)
        # Historical timestamps are explicit fixture metadata, not claimed capture dates.
        m=client.get('/api/memories/'+key).json();m['date']=date;server.write_memory(m)
        processing.append({'source':'pdf','ms':round((time.perf_counter()-start)*1000,2),'status':m['status'],'region_count':len(m['regions'])})
        rows=[]
        for query,expected in queries:
            start=time.perf_counter();response=client.get('/api/search',params={'q':query,'tz':'Asia/Karachi','library':'captures'});response.raise_for_status()
            result=response.json();latency=(time.perf_counter()-start)*1000
            names=[mapping[k] for k in result['ids']]
            rows.append({'query':query,'expected':expected,'retrieved':names,'top1':bool(names and names[0] in expected) if expected else not names,'top3':bool(set(names[:3])&set(expected)) if expected else not names,'ms':round(latency,2),'mode':result['mode']})
        positive=[r for r in rows if r['expected']]
        negative=[r for r in rows if not r['expected']]
        report={'timestamp':datetime.now().astimezone().isoformat(),'hardware':{'cpu':platform.processor(),'ram_gib':round(psutil.virtual_memory().total/1024**3,1),'os':platform.platform(),'python':platform.python_version(),'inference_device':'CPU'},'models':status,'dataset':'4 actual browser screenshots of authored local pages + 1 imported authored PDF; simulated Tuesday timestamps in isolated evaluation DB','network':'Non-loopback socket connections blocked; loopback permitted','external_connection_attempts':attempts,'metrics':{'positive_queries':len(positive),'top1_accuracy':sum(r['top1'] for r in positive)/len(positive),'top3_accuracy':sum(r['top3'] for r in positive)/len(positive),'no_match_correct':sum(r['top1'] for r in negative),'no_match_queries':len(negative),'median_search_ms':round(statistics.median(r['ms'] for r in rows),2),'max_search_ms':max(r['ms'] for r in rows)},'processing':processing,'queries':rows}
        (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
