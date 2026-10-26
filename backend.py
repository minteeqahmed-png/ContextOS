"""Local capture, durable processing, and evidence retrieval for ContextOS."""
import sys
from pathlib import Path
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'.runtime'))
import asyncio
import base64
import importlib.util
import json
import re
import sqlite3
import threading
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import os
from local_config import load_local_env
load_local_env()
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field, field_validator
import extraction
import retrieval
import vision_privacy as vp

DB_PATH=Path(os.environ.get('CONTEXTOS_DB',ROOT/'data'/'memories.sqlite3'))
OLLAMA=vp.config()['local']
VISION_MODEL=vp.config()['local_model']
EMBED_MODEL=os.environ.get('CONTEXTOS_EMBED_MODEL','nomic-embed-text')
pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='contextos-index')
vision_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='contextos-vision')
jobs={}
vision_jobs={}
job_lock=threading.RLock()


def searchable(m):
    return ' '.join(str(m.get(k,'')) for k in ('title','text','ocr_text','visual_description','origin','tags','session'))


@contextmanager
def database(path=None):
    target=Path(path or DB_PATH)
    target.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(target,timeout=20)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA secure_delete=ON')
    try:
        db.execute('CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, body TEXT NOT NULL, vector TEXT)')
        db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS recall USING fts5(id UNINDEXED, content)')
        db.execute('CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY, data BLOB, mime TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS work(id TEXT, kind TEXT, revision TEXT, state TEXT, PRIMARY KEY(id,kind))')
        db.execute('CREATE TABLE IF NOT EXISTS privacy(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS grounding(id TEXT PRIMARY KEY, memory_id TEXT, body TEXT NOT NULL)')
        if not db.execute("SELECT 1 FROM metadata WHERE key='initialized'").fetchone():
            if (ROOT/'seeds.json').exists():
                for m in json.loads((ROOT/'seeds.json').read_text(encoding='utf-8')):
                    db.execute('INSERT OR IGNORE INTO memories VALUES(?,?,NULL)',(m['id'],json.dumps(m)))
                    db.execute('INSERT INTO recall VALUES(?,?)',(m['id'],searchable(m)))
            db.execute("INSERT INTO metadata VALUES('initialized','true')")
        db.commit()
        yield db
        db.commit()
    finally:
        db.close()


def read_memory(key,path=None):
    with database(path) as db:
        row=db.execute('SELECT body FROM memories WHERE id=?',(key,)).fetchone()
        return json.loads(row['body']) if row else None


def write_memory(m,vector=None,path=None,expected=None):
    with database(path) as db:
        db.execute('BEGIN IMMEDIATE')
        if expected:
            row=db.execute('SELECT body FROM memories WHERE id=?',(m['id'],)).fetchone()
            if not row or json.loads(row['body']).get('revision')!=expected:
                return False
            m['saved']=json.loads(row['body']).get('saved',False)
        if vector is None:
            previous=db.execute('SELECT vector FROM memories WHERE id=?',(m['id'],)).fetchone()
            if previous and previous['vector']:vector=json.loads(previous['vector'])
        db.execute('INSERT OR REPLACE INTO memories VALUES(?,?,?)',(m['id'],json.dumps(m),json.dumps(vector) if vector else None))
        db.execute('DELETE FROM recall WHERE id=?',(m['id'],))
        db.execute('INSERT INTO recall VALUES(?,?)',(m['id'],searchable(m)))
    return True


@asynccontextmanager
async def lifespan(app):
    with database() as db:
        pending=[json.loads(r['body']) for r in db.execute('SELECT body FROM memories')]
    for m in pending:
        if m.get('status') in ('captured','extracting','indexing'):
            enqueue(m['id'])
        elif m.get('stages',{}).get('vision')=='queued':
            queue_vision_record(m,str(DB_PATH))
    with database() as db:
        vision_pending=[r['id'] for r in db.execute("SELECT id FROM work WHERE kind='vision' AND state IN ('queued','running')")]
    for key in vision_pending:
        enqueue_vision(key,str(DB_PATH))
    yield


app=FastAPI(title='ContextOS',docs_url=None,redoc_url=None,lifespan=lifespan)


@app.middleware('http')
async def local_only(request:Request,call_next):
    host=request.headers.get('host','').split(':')[0]
    if host not in ('127.0.0.1','localhost','testserver'):
        return JSONResponse({'detail':'Only localhost is allowed'},403)
    origin=request.headers.get('origin')
    if origin and origin not in (f'http://{request.headers.get("host")}',f'https://{request.headers.get("host")}'):
        return JSONResponse({'detail':'Cross-origin requests are not allowed'},403)
    if request.headers.get('sec-fetch-site')=='cross-site':
        return JSONResponse({'detail':'Cross-site requests are not allowed'},403)
    try:
        if int(request.headers.get('content-length','0'))>13_000_000:
            return JSONResponse({'detail':'Capture exceeds 8 MB upload limit'},413)
    except ValueError:
        return JSONResponse({'detail':'Invalid length'},400)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    return response


class Memory(BaseModel):
    id:str=Field(default_factory=lambda:str(uuid.uuid4()),pattern=r'^[a-zA-Z0-9_-]+$',max_length=100)
    title:str=Field(default='Untitled capture',min_length=1,max_length=160)
    text:str=Field(default='',max_length=200000)
    description:str=Field(default='',max_length=5000)
    type:str='Documents'
    preview:str='doc'
    source:str=Field(default='Personal note',max_length=300)
    origin:str=Field(default='Personal capture',max_length=300)
    collection:str='Work projects'
    tags:list[str]=Field(default_factory=list,max_length=20)
    date:str=Field(default_factory=lambda:datetime.now(timezone.utc).isoformat())
    image:str|None=Field(default=None,max_length=12000000)
    sample:bool=False
    saved:bool=False
    session:str=Field(default='',max_length=120)
    source_url:str=Field(default='',max_length=2000)
    source_path:str=Field(default='',max_length=500)
    source_kind:str='note'
    page:int|None=Field(default=None,ge=1,le=10000)
    @field_validator('date')
    @classmethod
    def valid_date(cls,value):
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None:
            raise ValueError('Capture date must include timezone')
        return d.isoformat()
    @field_validator('source_url')
    @classmethod
    def valid_url(cls,value):
        if value and (urlparse(value).scheme not in ('http','https') or not urlparse(value).hostname or urlparse(value).username):
            raise ValueError('Source URL must be an HTTP(S) address without credentials')
        return value


def preferences():
    with database() as db:
        row=db.execute("SELECT value FROM metadata WHERE key='preferences'").fetchone()
    return json.loads(row['value']) if row else {'exclusions':[]}


class Preferences(BaseModel):
    exclusions:list[str]=Field(default_factory=list,max_length=50)
    @field_validator('exclusions')
    @classmethod
    def valid_exclusions(cls,values):
        if any(not v.strip() or len(v)>200 for v in values):
            raise ValueError('Exclusion entries must contain 1–200 characters')
        return list(dict.fromkeys(v.strip().lower() for v in values))


@app.get('/api/preferences')
def get_preferences():
    return preferences()


@app.put('/api/preferences')
def save_preferences(value:Preferences):
    with database() as db:
        db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)',('preferences',value.model_dump_json()))
    return value


def check_excluded(m):
    context=' '.join(m.get(k,'') for k in ('source','origin','source_url','source_path','title')).lower()
    if any(rule in context for rule in preferences()['exclusions']):
        raise HTTPException(403,'This source matches an exclusion. Nothing was saved.')


async def model_list():
    try:
        async with httpx.AsyncClient(timeout=1,trust_env=False) as client:
            r=await client.get(OLLAMA+'/api/tags');r.raise_for_status()
            return [m['name'].removesuffix(':latest') for m in r.json().get('models',[])]
    except (httpx.HTTPError,ValueError,KeyError):
        return []


async def embed(text):
    try:
        async with httpx.AsyncClient(timeout=30,trust_env=False) as client:
            r=await client.post(OLLAMA+'/api/embed',json={'model':EMBED_MODEL,'input':text[:12000]});r.raise_for_status()
            return r.json()['embeddings'][0]
    except (httpx.HTTPError,ValueError,KeyError,IndexError):
        return None


@app.get('/api/status')
async def status():
    models=await model_list()
    c=vp.config()
    return {'storage':'sqlite','vision':VISION_MODEL in models,'embeddings':EMBED_MODEL in models,'local':c['mode']=='LOCAL_ONLY','mode':c['mode'],'review_policy':c['policy'],'remote_configured':bool(os.environ.get('OPENROUTER_API_KEY' if c['provider']=='openrouter' else 'CONTEXTOS_VISION_API_KEY')),'remote_model':c['model'],'local_model':c['local_model'],'upstream':c['upstream'],'ocr':bool(importlib.util.find_spec('rapidocr_onnxruntime')),'pdf':bool(importlib.util.find_spec('fitz')),'models':models}


@app.get('/api/memories')
def get_memories():
    with database() as db:
        return [json.loads(r['body']) for r in db.execute('SELECT body FROM memories')]


@app.get('/api/memories/{key}')
def get_memory(key:str):
    m=read_memory(key)
    if not m:raise HTTPException(404,'Memory not found')
    return m


def new_capture(item,regions=None):
    item.update(revision=str(uuid.uuid4()),status='captured',stages={'extraction':'pending','vision':'pending','embedding':'pending'},issues=[],regions=regions or [],ocr_text='\n'.join(r['text'] for r in regions or []),visual_description='')
    item['accepted_at']=time.time()
    item['telemetry']={}
    return item


def persist_capture(item,started,raw=None):
    # Artifact, searchable metadata and durable job are committed atomically.
    with database() as db:
        db.execute('INSERT INTO memories VALUES(?,?,NULL)',(item['id'],json.dumps(item)))
        db.execute('INSERT INTO recall VALUES(?,?)',(item['id'],searchable(item)))
        db.execute('INSERT INTO work VALUES(?,?,?,?)',(item['id'],'local',item['revision'],'queued'))
        if raw is not None:
            db.execute('INSERT INTO artifacts VALUES(?,?,?)',(item['id'],raw,'application/pdf'))
    item['telemetry']['capture_ack_ms']=round((time.perf_counter()-started)*1000,2)
    write_memory(item,expected=item['revision'])
    enqueue(item['id'])
    return item


@app.post('/api/memories')
def save_memory(memory:Memory):
    started=time.perf_counter()
    item=memory.model_dump()
    check_excluded(item)
    old=read_memory(item['id'])
    if old:
        # Old clients send full objects to bookmark. Preserve all derived evidence.
        if all(item.get(k)==old.get(k) for k in ('title','text','image')):
            with database() as db:
                db.execute('BEGIN IMMEDIATE')
                latest=db.execute('SELECT body FROM memories WHERE id=?',(item['id'],)).fetchone()
                if not latest:raise HTTPException(404,'Memory was deleted')
                old=json.loads(latest['body'])
                old['saved']=item['saved']
                db.execute('UPDATE memories SET body=? WHERE id=?',(json.dumps(old),item['id']))
            return old
        raise HTTPException(409,'Existing captures are immutable. Save a new capture or reprocess this one.')
    if item.get('image'):
        try:
            if not re.match(r'^data:image/(png|jpeg|webp);base64,',item['image']):raise ValueError('Unsupported image type')
            extraction.image_bytes(item['image'])
        except Exception as e:
            raise HTTPException(422,'Invalid or oversized image') from e
    if not item['text'].strip() and not item.get('image'):
        raise HTTPException(422,'Add text or an image')
    new_capture(item)
    return persist_capture(item,started)


class PDFImport(BaseModel):
    data:str=Field(max_length=12000000)
    filename:str=Field(default='document.pdf',max_length=250)
    page:int=Field(default=1,ge=1,le=10000)
    session:str=Field(default='',max_length=120)
    source_url:str=''
    text:str=Field(default='',max_length=200000)


@app.post('/api/import/pdf')
def import_pdf(value:PDFImport):
    started=time.perf_counter()
    name=Path(value.filename).name
    item=Memory(title=f'{name} · page {value.page}'[:160],origin=name,source_path=name,source='PDF import',source_kind='pdf',page=value.page,session=value.session,source_url=value.source_url,text=value.text).model_dump()
    check_excluded(item)
    try:
        raw=base64.b64decode(value.data.split(',')[-1],validate=True)
        if len(raw)>8*1024*1024:raise ValueError('PDF exceeds 8 MB')
        if not raw.startswith(b'%PDF'):raise ValueError('Invalid PDF header')
    except ImportError as e:
        raise HTTPException(503,'Install the local PDF dependencies first') from e
    except Exception as e:
        raise HTTPException(422,str(e)) from e
    item['has_original']=True
    new_capture(item)
    return persist_capture(item,started,raw)


def enqueue(key):
    path=str(DB_PATH)
    with job_lock:
        job=(path,key)
        if job in jobs and not jobs[job].done():return
        jobs[job]=pool.submit(process_memory,key,path)


def process_memory(key,path):
    m=read_memory(key,path)
    if not m:return
    revision=m['revision']
    def commit(state):
        m['status']=state
        return write_memory(m,path=path,expected=revision)
    try:
        if not commit('extracting'):return
        with database(path) as db:
            db.execute("UPDATE work SET state='running' WHERE id=? AND kind='local'",(key,))
        m['issues']=[]
        if m.get('has_original') and not m.get('image'):
            with database(path) as db:
                source=db.execute('SELECT data FROM artifacts WHERE id=?',(key,)).fetchone()
            m['image'],m['regions'],m['page_count']=extraction.render_pdf(bytes(source['data']),m['page'])
        if m.get('image'):
            try:
                if not m.get('regions') or m['regions'][0].get('method')!='pdf-text':
                    m['regions']=extraction.extract_image(m['image'])
                elif vp.config()['mode']=='HYBRID_SANITIZED':
                    # PDF text alone misses secrets embedded in raster graphics.
                    m['privacy_regions']=extraction.extract_image(m['image'])
                m['ocr_text']='\n'.join(r['text'] for r in m['regions'])
                m['stages']['extraction']='ready' if m['regions'] else 'empty'
                if not m['regions']:m['issues'].append('No readable text found. Add a new capture with an annotation or retry a clearer frame.')
            except Exception as e:
                m['stages']['extraction']='failed'
                m['issues'].append('Local OCR failed: '+type(e).__name__+'. Install dependencies or retry a clearer frame.')
            m['ocr_text']='\n'.join(r['text'] for r in m.get('regions',[]))
        else:m['stages']['extraction']='not-needed'
        m.setdefault('telemetry',{})['extraction_finished_ms']=round((time.time()-m.get('accepted_at',time.time()))*1000,2)
        if m.get('text') or m.get('ocr_text'):
            m['telemetry']['text_ready_ms']=m['telemetry']['extraction_finished_ms']
        if m.get('image'):
            m['phash']=vp.phash(m['image'])
            with database(path) as db:
                others=[json.loads(r['body']) for r in db.execute('SELECT body FROM memories WHERE id!=?',(key,))]
            m['near_duplicates']=[o['id'] for o in others if o.get('phash') and o.get('session')==m.get('session') and (int(o['phash'],16)^int(m['phash'],16)).bit_count()<=4]
        # Publish OCR before any model call; remote review never blocks local recall.
        if not commit('indexing'):return
        models=asyncio.run(model_list())
        c=vp.config()
        m['stages']['vision']=('PENDING_PRIVACY_REVIEW' if c['mode']=='HYBRID_SANITIZED' else 'queued' if VISION_MODEL in models else 'unavailable') if m.get('image') else 'not-needed'
        vectors=[]
        if EMBED_MODEL in models:
            chunks=[searchable(m)]+[r['text'] for r in m.get('regions',[])][:80]
            for text in chunks:
                vector=asyncio.run(embed(text))
                if vector:vectors.append(vector)
                else:
                    m['issues'].append('Embedding failed. Keyword evidence remains searchable.');break
            m['stages']['embedding']='ready' if len(vectors)==len(chunks) else 'failed'
        else:m['stages']['embedding']='unavailable'
        m['description']=(m.get('ocr_text') or m.get('text') or m.get('visual_description') or 'Frame saved; no searchable text extracted.')[:180]
        m['status']='ready' if (m.get('text') or m.get('ocr_text') or m.get('visual_description')) else 'failed'
        m['processed_at']=datetime.now(timezone.utc).isoformat()
        if not write_memory(m,vectors or None,path,revision):return
        with database(path) as db:
            db.execute("UPDATE work SET state='done' WHERE id=? AND kind='local' AND revision=?",(key,revision))
        if m['stages']['vision']=='queued':
            queue_vision_record(m,path)
        elif m['stages']['vision']=='PENDING_PRIVACY_REVIEW':
            try:
                proposal=prepare_privacy(m,[],path)
                # Even allowlisted fixtures cannot bypass failed/uncertain extraction.
                if vp.fixture_allowed(m['image'],c) and not proposal['warnings'] and m['stages']['extraction']=='ready':
                    approve_privacy_record(m,proposal['digest'],path)
            except Exception:
                # Remain local and reviewable, including when fixture config is invalid.
                pass
    except Exception as e:
        m['issues'].append('Processing interrupted: '+type(e).__name__+'. Retry processing.');m['status']='failed'
        write_memory(m,path=path,expected=revision)
        with database(path) as db:
            db.execute("UPDATE work SET state='failed' WHERE id=? AND kind='local' AND revision=?",(key,revision))


def queue_vision_record(m,path):
    with database(path) as db:
        if not db.execute('SELECT 1 FROM memories WHERE id=?',(m['id'],)).fetchone():return
        db.execute('INSERT OR REPLACE INTO work VALUES(?,?,?,?)',(m['id'],'vision',m['revision'],'queued'))
    enqueue_vision(m['id'],path)


def enqueue_vision(key,path):
    with job_lock:
        job=(path,key)
        if job in vision_jobs and not vision_jobs[job].done():return
        vision_jobs[job]=vision_pool.submit(process_vision,key,path)


def process_vision(key,path):
    m=read_memory(key,path)
    if not m:return
    revision=m['revision']
    try:
        c=vp.config()
        if c['mode']=='HYBRID_SANITIZED':
            with database(path) as db:
                row=db.execute('SELECT body FROM privacy WHERE id=?',(key,)).fetchone()
            p=json.loads(row['body']) if row else {}
            if p.get('state')!='approved' or p.get('revision')!=revision:raise ValueError('Approval missing')
            body,boundary=p['payload'],p['target']
        else:
            body,boundary=vp.payload(m['image'],vp.DESCRIBE,c),vp.target(c)
        m['stages']['vision']='running'
        if not write_memory(m,path=path,expected=revision):return
        with database(path) as db:
            db.execute("UPDATE work SET state='running' WHERE id=? AND kind='vision'",(key,))
        started=time.perf_counter()
        descriptor,region_warnings=vp.parse_descriptor(vp.infer(body,boundary))
        m['issues'].extend(region_warnings)
        m['visual_descriptor']=descriptor
        m['vision_provenance']={'model':c['local_model'] if c['mode']=='LOCAL_ONLY' else c['model'],'provider':c['provider'] if c['mode']!='LOCAL_ONLY' else 'ollama','mode':c['mode']}
        m['visual_description']='\n'.join([descriptor['summary']]+[e['description'] for e in descriptor['entities']]+descriptor['relationships'])
        m['visual_regions']=[{'id':'visual-'+str(i),'text':e['description'],'box':e['box'],'method':'vision-inferred'} for i,e in enumerate(descriptor['entities'])]
        m['stages']['vision']='ready'
        m.setdefault('telemetry',{})['vision_inference_ms']=round((time.perf_counter()-started)*1000,2)
        m['status']='ready'
        vectors=[]
        if EMBED_MODEL in asyncio.run(model_list()):
            for text in [searchable(m)]+[r['text'] for r in m.get('regions',[])+m['visual_regions']][:80]:
                vector=asyncio.run(embed(text))
                if vector:vectors.append(vector)
            m['stages']['embedding']='ready' if vectors else 'failed'
        else:
            with database(path) as db:
                row=db.execute('SELECT vector FROM memories WHERE id=?',(key,)).fetchone()
                vectors=json.loads(row['vector']) if row and row['vector'] else []
        m['telemetry']['vision_ready_ms']=round((time.time()-m.get('accepted_at',time.time()))*1000,2)
        write_memory(m,vectors or None,path,revision)
    except Exception as e:
        m['stages']['vision']='failed'
        m['issues'].append('Vision enrichment failed ('+type(e).__name__+'). Check provider configuration and review again. Local evidence is preserved.')
        write_memory(m,path=path,expected=revision)
    finally:
        with database(path) as db:
            db.execute('UPDATE work SET state=? WHERE id=? AND kind=? AND revision=?',('done' if m['stages']['vision']=='ready' else 'failed',key,'vision',revision))


def prepare_privacy(m,masks,path):
    if not m.get('image'):raise HTTPException(409,'No rendered frame is available yet')
    if m.get('status') in ('captured','extracting','indexing'):raise HTTPException(409,'Wait for local extraction to finish')
    c=vp.config()
    if c['mode']!='HYBRID_SANITIZED':raise HTTPException(409,'Remote review is disabled in LOCAL_ONLY')
    image,all_masks,warnings=vp.redact(m['image'],m.get('regions',[])+m.get('privacy_regions',[]),masks)
    if m.get('stages',{}).get('extraction')!='ready':warnings.append('OCR failed or found no text. Inspect and mask the entire frame before approving.')
    p={'image':image,'masks':all_masks,'warnings':warnings,'target':vp.target(c),'payload':vp.payload(image,vp.DESCRIBE,c),'revision':m['revision'],'state':'pending'}
    p['digest']=vp.digest(p)
    with database(path) as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT body FROM privacy WHERE id=?',(m['id'],)).fetchone()
        if existing and json.loads(existing['body']).get('state')=='approved':raise HTTPException(409,'Artifact already approved. Reprocess to revoke approval and review again.')
        current=db.execute('SELECT body FROM memories WHERE id=?',(m['id'],)).fetchone()
        if not current or json.loads(current['body']).get('revision')!=m['revision']:raise HTTPException(409,'Capture changed; reopen review')
        db.execute('INSERT OR REPLACE INTO privacy VALUES(?,?)',(m['id'],json.dumps(p)))
    return p


class Masks(BaseModel):
    masks:list[list[float]]=Field(default_factory=list,max_length=100)


class Approval(BaseModel):
    digest:str=Field(max_length=64,min_length=64)


@app.post('/api/memories/{key}/privacy/prepare')
def privacy_prepare(key:str,value:Masks):
    try:return prepare_privacy(get_memory(key),value.masks,str(DB_PATH))
    except ValueError as e:raise HTTPException(422,str(e)) from e


def approve_privacy_record(m,digest,path):
    with database(path) as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT body FROM privacy WHERE id=?',(m['id'],)).fetchone()
        p=json.loads(row['body']) if row else {}
        current=db.execute('SELECT body FROM memories WHERE id=?',(m['id'],)).fetchone()
        if not current:raise HTTPException(404,'Memory deleted')
        m=json.loads(current['body'])
        if p.get('digest')!=digest or p.get('revision')!=m['revision'] or p.get('state')!='pending' or p.get('target')!=vp.target(vp.config()):
            raise HTTPException(409,'Review is stale or already approved; prepare again')
        p['state']='approved';p['approved_at']=time.time()
        m['stages']['vision']='queued'
        m['privacy_state']='approved'
        db.execute('UPDATE privacy SET body=? WHERE id=?',(json.dumps(p),m['id']))
        db.execute('UPDATE memories SET body=? WHERE id=?',(json.dumps(m),m['id']))
        db.execute('INSERT OR REPLACE INTO work VALUES(?,?,?,?)',(m['id'],'vision',m['revision'],'queued'))
    enqueue_vision(m['id'],path)
    return {'approved':True}


@app.post('/api/memories/{key}/privacy/approve')
def privacy_approve(key:str,value:Approval):
    return approve_privacy_record(get_memory(key),value.digest,str(DB_PATH))


@app.post('/api/memories/{key}/privacy/local-only')
def keep_local(key:str):
    with job_lock:
        m=get_memory(key)
        if m.get('status') in ('captured','extracting','indexing') or any(f and not f.done() for f in [vision_jobs.get((str(DB_PATH),key))]):
            raise HTTPException(409,'Processing is active. Wait until it finishes before changing this frame.')
        m['privacy_state']='local-only';m['stages']['vision']='skipped'
        write_memory(m,expected=m['revision'])
        with database() as db:
            db.execute('DELETE FROM privacy WHERE id=?',(key,))
            db.execute('DELETE FROM grounding WHERE memory_id=?',(key,))
            db.execute("DELETE FROM work WHERE id=? AND kind='vision'",(key,))
    return {'local_only':True}


@app.post('/api/memories/{key}/reprocess')
def reprocess(key:str):
    with job_lock:
        m=get_memory(key)
        pending=jobs.get((str(DB_PATH),key))
        if pending and not pending.done():raise HTTPException(409,'This memory is already processing')
        vision_pending=vision_jobs.get((str(DB_PATH),key))
        if vision_pending and not vision_pending.done():raise HTTPException(409,'Vision is still processing')
        m['revision']=str(uuid.uuid4());m['status']='captured'
        m.setdefault('stages',{});m['issues']=[]
        write_memory(m)
        with database() as db:
            db.execute('DELETE FROM privacy WHERE id=?',(key,))
            db.execute('DELETE FROM grounding WHERE memory_id=?',(key,))
            db.execute("DELETE FROM work WHERE id=? AND kind='vision'",(key,))
            db.execute('INSERT OR REPLACE INTO work VALUES(?,?,?,?)',(key,'local',m['revision'],'queued'))
        enqueue(key)
    return m


@app.get('/api/memories/{key}/original')
def original(key:str):
    with database() as db:
        row=db.execute('SELECT data,mime FROM artifacts WHERE id=?',(key,)).fetchone()
    if not row:raise HTTPException(404,'No original document is stored for this memory')
    return Response(bytes(row['data']),media_type=row['mime'],headers={'Content-Disposition':'inline; filename="source.pdf"'})


@app.delete('/api/memories/{key}')
def delete_memory(key:str):
    with database() as db:
        db.execute('DELETE FROM recall WHERE id=?',(key,))
        db.execute('DELETE FROM artifacts WHERE id=?',(key,))
        db.execute('DELETE FROM privacy WHERE id=?',(key,))
        db.execute('DELETE FROM grounding WHERE memory_id=?',(key,))
        db.execute('DELETE FROM work WHERE id=?',(key,))
        count=db.execute('DELETE FROM memories WHERE id=?',(key,)).rowcount
    if not count:raise HTTPException(404,'Memory not found')
    return {'deleted':True}


class GroundQuestion(BaseModel):
    query:str=Field(min_length=1,max_length=2000)


@app.post('/api/memories/{key}/grounding/prepare')
def prepare_grounding(key:str,value:GroundQuestion):
    m=get_memory(key);c=vp.config()
    if not m.get('image'):raise HTTPException(409,'No frame available')
    if c['mode']=='HYBRID_SANITIZED':
        with database() as db:
            row=db.execute('SELECT body FROM privacy WHERE id=?',(key,)).fetchone()
        approved=json.loads(row['body']) if row else {}
        if approved.get('state')!='approved' or approved.get('revision')!=m['revision'] or approved.get('target')!=vp.target(c):
            raise HTTPException(409,'Approve this frame for the current provider before visual verification')
        image=approved['image']
    else:image=m['image']
    query=vp.sanitize_text(value.query)
    p={'id':str(uuid.uuid4()),'memory_id':key,'revision':m['revision'],'image':image,'query':query,'payload':vp.payload(image,vp.GROUND+query,c),'target':vp.target(c),'created':time.time(),'state':'pending'}
    p['digest']=vp.digest(p)
    with database() as db:
        db.execute('DELETE FROM grounding WHERE memory_id=?',(key,))
        db.execute('INSERT INTO grounding VALUES(?,?,?)',(p['id'],key,json.dumps(p)))
    return p


@app.post('/api/grounding/{proposal}/approve')
def approve_grounding(proposal:str,value:Approval):
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT body FROM grounding WHERE id=?',(proposal,)).fetchone()
        p=json.loads(row['body']) if row else {}
        if p.get('state')!='pending' or p.get('digest')!=value.digest or time.time()-p.get('created',0)>900:
            raise HTTPException(409,'Query review expired or already used')
        row=db.execute('SELECT body FROM memories WHERE id=?',(p['memory_id'],)).fetchone()
        m=json.loads(row['body']) if row else {}
        if m.get('revision')!=p['revision'] or p['target']!=vp.target(vp.config()):raise HTTPException(409,'Capture or provider changed')
        if p['target']['mode']=='HYBRID_SANITIZED':
            row=db.execute('SELECT body FROM privacy WHERE id=?',(p['memory_id'],)).fetchone()
            approval=json.loads(row['body']) if row else {}
            if approval.get('state')!='approved' or approval.get('image')!=p['image']:raise HTTPException(409,'Frame approval revoked')
        p['state']='running'
        db.execute('UPDATE grounding SET body=? WHERE id=?',(json.dumps(p),proposal))
    try:
        started=time.perf_counter()
        result=vp.Grounding.model_validate(vp.infer(p['payload'],p['target'])).model_dump()
        result.update(memory_id=p['memory_id'],image=p['image'],query=p['query'],latency_ms=round((time.perf_counter()-started)*1000,2),interpretation='Model interpretation grounded in the displayed pixels; verify the highlighted regions.')
        return result
    except Exception as e:
        raise HTTPException(502,'Visual verification failed ('+type(e).__name__+'). No supported answer is available.') from e
    finally:
        with database() as db:
            db.execute('DELETE FROM grounding WHERE id=?',(proposal,))


@app.get('/api/search')
async def search(q:str='',tz:str='UTC',library:str='all',session:str=''):
    if len(q)>2000:raise HTTPException(422,'Query is too long')
    with database() as db:
        rows=db.execute('SELECT * FROM memories').fetchall()
    items=[json.loads(r['body']) for r in rows]
    items=[m for m in items if (library=='all' or (bool(m.get('sample'))==(library=='samples'))) and (not session or m.get('session')==session)]
    try:filters=retrieval.constraints(q,tz,items)
    except (ZoneInfoNotFoundError,ValueError):raise HTTPException(422,'Invalid timezone or calendar date')
    items=[m for m in items if retrieval.eligible(m,filters)]
    with database() as db:
        query=' OR '.join('"'+t+'"' for t in filters['terms'][:40])
        lexical=[r['id'] for r in db.execute('SELECT id FROM recall WHERE recall MATCH ? ORDER BY bm25(recall)',(query,))] if query else []
    vectors={}
    for row in rows:
        if row['vector']:
            vector=json.loads(row['vector']);vectors[row['id']]=vector if vector and isinstance(vector[0],list) else [vector]
    query_vector=await embed(q) if filters['terms'] and any(m['id'] in vectors for m in items) else None
    results=retrieval.rank(items,filters,lexical,vectors,query_vector)
    return {'ids':[r['id'] for r in results],'results':results,'mode':'hybrid' if query_vector else 'text','constraints':filters['labels'],'timezone':tz}


@app.get('/')
def index():return FileResponse(ROOT/'index.html')


@app.get('/demo/{name}')
def demo_source(name:str):
    if name not in {'pricing.html','growth.html','code.html','other-pricing.html','pricing.pdf','visual-dip.png','visual-rise.png','visual-layout.png'}:
        raise HTTPException(404)
    path=ROOT/'evaluation'/'sources'/name
    if not path.exists():raise HTTPException(404)
    return FileResponse(path)


@app.get('/{filename}')
def static_file(filename:str):
    if filename not in {'app.js','style.css','evidence.js','privacy-ui.js'}:raise HTTPException(404)
    return FileResponse(ROOT/filename)
