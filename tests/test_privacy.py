import base64
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from PIL import Image
from fastapi.testclient import TestClient
import server
import vision_privacy as vp


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        server.DB_PATH=Path(self.temp.name)/'privacy.sqlite3'
        self.env=patch.dict(os.environ,{'CONTEXTOS_MODE':'HYBRID_SANITIZED','CONTEXTOS_REVIEW_POLICY':'interactive','CONTEXTOS_OPENROUTER_PROVIDER':'test-provider'})
        self.env.start()
        self.models=patch.object(server,'model_list',AsyncMock(return_value=[]));self.models.start()
        self.ocr=patch.object(server.extraction,'extract_image',return_value=[{'id':'0','text':'alice@example.com','box':[.1,.1,.7,.3],'confidence':.99,'method':'local-ocr'}]);self.ocr.start()
        self.client=TestClient(server.app)
        b=io.BytesIO();Image.new('RGB',(100,100),'white').save(b,format='PNG')
        self.image='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

    def tearDown(self):
        for mapping in (server.jobs,server.vision_jobs):
            for (path,_),future in list(mapping.items()):
                if path==str(server.DB_PATH):future.result(timeout=30)
        self.client.close();self.ocr.stop();self.models.stop();self.env.stop();self.temp.cleanup()

    def capture(self):
        response=self.client.post('/api/memories',json={'title':'Fixture','image':self.image,'session':'demo'})
        self.assertEqual(response.status_code,200,response.text)
        key=response.json()['id'];server.jobs[(str(server.DB_PATH),key)].result(timeout=30)
        return key

    def prepare(self,key,masks=None):
        r=self.client.post(f'/api/memories/{key}/privacy/prepare',json={'masks':masks or []})
        self.assertEqual(r.status_code,200,r.text)
        return r.json()

    def test_capture_ack_precedes_blocked_ocr_and_job_is_durable(self):
        entered=threading.Event();release=threading.Event()
        def blocked(data):entered.set();release.wait(10);return []
        with patch.object(server.extraction,'extract_image',side_effect=blocked):
            r=self.client.post('/api/memories',json={'title':'Durable','image':self.image})
            try:
                self.assertEqual(r.status_code,200);self.assertIn('capture_ack_ms',r.json()['telemetry'])
                self.assertTrue(entered.wait(5))
                with server.database() as db:
                    self.assertIsNotNone(db.execute('SELECT * FROM work WHERE id=?',(r.json()['id'],)).fetchone())
                self.assertTrue(server.read_memory(r.json()['id'])['image'])
            finally:release.set()
            server.jobs[(str(server.DB_PATH),r.json()['id'])].result(timeout=30)

    def test_gate_masks_original_unchanged_and_no_network(self):
        with patch.object(vp,'infer',side_effect=AssertionError('Unapproved upload')) as inference:
            key=self.capture();p=self.prepare(key,[[.8,.8,.95,.95]])
            m=server.read_memory(key)
            self.assertEqual(m['image'],self.image)
            self.assertIn('alice@example.com',m['ocr_text'])
            self.assertEqual(m['stages']['vision'],'PENDING_PRIVACY_REVIEW')
            im=Image.open(io.BytesIO(base64.b64decode(p['image'].split(',')[1])))
            self.assertEqual(im.getpixel((20,20)),(0,0,0));self.assertEqual(im.getpixel((90,90)),(0,0,0))
            self.assertNotIn('alice@example.com',json.dumps(p['payload']))
            self.assertFalse(inference.called)
            found=self.client.get('/api/search',params={'q':'alice','library':'captures'}).json()
            self.assertIn(key,found['ids'])

    def test_stale_approval_rejected_and_local_only_skips(self):
        key=self.capture();p=self.prepare(key);self.prepare(key,[[0,0,1,1]])
        r=self.client.post(f'/api/memories/{key}/privacy/approve',json={'digest':p['digest']})
        self.assertEqual(r.status_code,409)
        self.assertEqual(self.client.post(f'/api/memories/{key}/privacy/local-only').status_code,200)
        self.assertEqual(server.read_memory(key)['stages']['vision'],'skipped')
        self.assertEqual(self.client.post(f'/api/memories/{key}/grounding/prepare',json={'query':'status?'}).status_code,409)

    def test_approved_artifact_reused_for_grounding_and_query_sanitized(self):
        key=self.capture();p=self.prepare(key)
        descriptor={'summary':'Green line dips then spikes','entities':[{'id':'a','description':'Green line dips','box':[.1,.4,.9,.8]}],'relationships':[]}
        with patch.object(vp,'infer',return_value=descriptor) as inference:
            r=self.client.post(f'/api/memories/{key}/privacy/approve',json={'digest':p['digest']});self.assertEqual(r.status_code,200)
            server.vision_jobs[(str(server.DB_PATH),key)].result(timeout=30)
            self.assertEqual(inference.call_args.args[0],p['payload'])
        self.assertIn('Green',server.read_memory(key)['visual_description'])
        q=self.client.post(f'/api/memories/{key}/grounding/prepare',json={'query':'Does alice@example.com correspond to this green line?'}).json()
        self.assertEqual(q['image'],p['image']);self.assertNotIn('alice@example.com',json.dumps(q['payload']))
        result={'answer':'The evidence is masked','supported':False,'citations':[]}
        with patch.object(vp,'infer',return_value=result) as inference:
            r=self.client.post(f"/api/grounding/{q['id']}/approve",json={'digest':q['digest']})
            self.assertEqual(r.status_code,200,r.text);self.assertFalse(r.json()['supported'])
            self.assertEqual(inference.call_args.args[0],q['payload'])
        self.assertEqual(self.client.post(f"/api/grounding/{q['id']}/approve",json={'digest':q['digest']}).status_code,409)

    def test_failed_ocr_never_uploads_and_retains_frame(self):
        with patch.object(server.extraction,'extract_image',side_effect=TimeoutError),patch.object(vp,'infer') as inference:
            key=self.capture();p=self.prepare(key)
            self.assertTrue(p['warnings']);self.assertFalse(inference.called)
            self.assertEqual(server.read_memory(key)['image'],self.image)

    def test_fixture_flag_rejected_outside_explicit_test_run(self):
        with patch.dict(os.environ,{'CONTEXTOS_REVIEW_POLICY':'auto_approve_sanitized','CONTEXTOS_TEST_RUN':'0'}):
            with self.assertRaises(ValueError):vp.config()

    def test_duplicate_frames_retained_and_delete_cascades(self):
        first=self.capture();second=self.capture()
        self.assertIn(first,server.read_memory(second)['near_duplicates'])
        self.assertIsNotNone(server.read_memory(first));self.prepare(second)
        self.client.delete('/api/memories/'+second)
        with server.database() as db:
            for table in ('privacy','work','recall'):
                self.assertIsNone(db.execute(f'SELECT * FROM {table} WHERE id=?',(second,)).fetchone())

    def test_grounding_requires_distinct_valid_citations(self):
        with self.assertRaises(ValueError):
            vp.Grounding.model_validate({'answer':'Yes','supported':True,'citations':[{'description':'one','box':[0,0,1,1]}]})

    def test_provider_change_invalidates_review(self):
        key=self.capture();p=self.prepare(key)
        with patch.dict(os.environ,{'CONTEXTOS_VISION_MODEL':'changed'}):
            self.assertEqual(self.client.post(f'/api/memories/{key}/privacy/approve',json={'digest':p['digest']}).status_code,409)

    def test_fixture_bypass_requires_hash_and_no_risk_warnings(self):
        manifest=Path(self.temp.name)/'manifest.json'
        manifest.write_text(json.dumps({'image_sha256':[vp.raw_hash(self.image)]}))
        env={'CONTEXTOS_TEST_RUN':'1','CONTEXTOS_DB':str(server.DB_PATH),'CONTEXTOS_FIXTURE_MANIFEST':str(manifest),'CONTEXTOS_REVIEW_POLICY':'auto_approve_sanitized'}
        with patch.dict(os.environ,env),patch.object(vp,'infer') as inference:
            key=self.capture()  # email detected; hash alone must not bypass review
            self.assertEqual(server.read_memory(key)['stages']['vision'],'PENDING_PRIVACY_REVIEW')
            self.assertFalse(inference.called)
        safe=[{'id':'0','text':'Workspace','box':[0,0,.5,.1],'confidence':1,'method':'local-ocr'}]
        with patch.dict(os.environ,env),patch.object(server.extraction,'extract_image',return_value=safe),patch.object(vp,'infer',return_value={'summary':'Empty white workspace','entities':[],'relationships':[]}) as inference:
            key=self.capture();server.vision_jobs[(str(server.DB_PATH),key)].result(timeout=30)
            self.assertTrue(inference.called);self.assertEqual(server.read_memory(key)['stages']['vision'],'ready')

    def test_restart_resumes_durable_capture(self):
        with patch.object(server,'enqueue'):
            response=self.client.post('/api/memories',json={'title':'Restart','image':self.image})
        key=response.json()['id']
        self.assertEqual(server.read_memory(key)['status'],'captured')
        with TestClient(server.app):
            server.jobs[(str(server.DB_PATH),key)].result(timeout=30)
        self.assertEqual(server.read_memory(key)['stages']['vision'],'PENDING_PRIVACY_REVIEW')

    def test_deleted_frame_cannot_be_approved(self):
        key=self.capture();p=self.prepare(key)
        self.client.delete('/api/memories/'+key)
        with patch.object(vp,'infer') as inference:
            self.assertEqual(self.client.post(f'/api/memories/{key}/privacy/approve',json={'digest':p['digest']}).status_code,404)
            self.assertFalse(inference.called)


if __name__=='__main__':unittest.main()
