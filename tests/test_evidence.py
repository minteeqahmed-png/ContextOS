import base64
import io
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
import server
from PIL import Image
import fitz
import retrieval


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        server.DB_PATH=Path(self.temp.name)/'test.sqlite3'
        self.models=patch.object(server,'model_list',AsyncMock(return_value=[]));self.models.start()
        self.client=TestClient(server.app)

    def tearDown(self):
        for (path,key),future in list(server.jobs.items()):
            if path==str(server.DB_PATH):future.result(timeout=30)
        for (path,key),future in list(server.vision_jobs.items()):
            if path==str(server.DB_PATH):future.result(timeout=30)
        self.client.close();self.models.stop();self.temp.cleanup()

    def wait(self,key):
        server.jobs[(str(server.DB_PATH),key)].result(timeout=30)
        pending=server.vision_jobs.get((str(server.DB_PATH),key))
        if pending:pending.result(timeout=30)
        return self.client.get('/api/memories/'+key).json()

    def pdf(self,text='Pro plan price is $49 per month'):
        doc=fitz.open();p=doc.new_page();p.insert_text((50,90),text,fontsize=20)
        raw=doc.tobytes();doc.close()
        return {'data':base64.b64encode(raw).decode(),'filename':'pricing.pdf','page':1,'session':'Product meeting'}

    def image(self):
        b=io.BytesIO();Image.new('RGB',(300,150),'white').save(b,format='PNG')
        return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

    def test_pdf_evidence_original_and_cascade_delete(self):
        response=self.client.post('/api/import/pdf',json=self.pdf());self.assertEqual(response.status_code,200,response.text)
        key=response.json()['id'];m=self.wait(key)
        self.assertEqual(m['status'],'ready');self.assertIn('$49',m['ocr_text'])
        self.assertTrue(m['regions']);self.assertEqual(m['regions'][0]['method'],'pdf-text')
        for r in m['regions']:
            self.assertTrue(all(0<=p<=1 for p in r['box']))
        found=self.client.get('/api/search',params={'q':'Pro plan price in the PDF from product meeting','tz':'Asia/Karachi','library':'captures'}).json()
        self.assertEqual(found['ids'][0],key);self.assertTrue(found['results'][0]['region_ids'])
        self.assertEqual(self.client.get('/api/memories/'+key+'/original').content[:4],b'%PDF')
        self.client.delete('/api/memories/'+key)
        self.assertEqual(self.client.get('/api/memories/'+key+'/original').status_code,404)
        self.assertNotIn(key,self.client.get('/api/search',params={'q':'Pro price'}).json()['ids'])

    def test_failed_ocr_keeps_original_and_reprocess_recovers(self):
        with patch.object(server.extraction,'extract_image',side_effect=RuntimeError('test')):
            key=self.client.post('/api/memories',json={'title':'Unannotated frame','image':self.image()}).json()['id']
            m=self.wait(key)
        self.assertEqual(m['status'],'failed');self.assertTrue(m['image']);self.assertEqual(m['stages']['extraction'],'failed')
        with patch.object(server.extraction,'extract_image',return_value=[{'id':'0','text':'Recovery evidence','box':[.1,.1,.8,.3],'method':'local-ocr'}]):
            self.client.post('/api/memories/'+key+'/reprocess');m=self.wait(key)
        self.assertEqual(m['status'],'ready');self.assertIn('Recovery',m['ocr_text'])

    def test_delete_during_processing_does_not_resurrect(self):
        entered=threading.Event();resume=threading.Event()
        def extract(data):
            entered.set();resume.wait(10);return []
        with patch.object(server.extraction,'extract_image',side_effect=extract):
            key=self.client.post('/api/memories',json={'title':'Race test','image':self.image()}).json()['id']
            self.assertTrue(entered.wait(10));self.client.delete('/api/memories/'+key);resume.set()
            server.jobs[(str(server.DB_PATH),key)].result(timeout=20)
        self.assertEqual(self.client.get('/api/memories/'+key).status_code,404)

    def test_exclusion_and_url_validation(self):
        self.client.put('/api/preferences',json={'exclusions':['private.example']})
        response=self.client.post('/api/memories',json={'title':'Test','text':'Content','source_url':'https://private.example/doc'})
        self.assertEqual(response.status_code,403)
        self.assertEqual(self.client.post('/api/memories',json={'title':'Test','text':'Text','source_url':'javascript:alert(1)'}).status_code,422)
        response=self.client.post('/api/import/pdf',json={**self.pdf(),'page':2})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.wait(response.json()['id'])['status'],'failed')

    def test_local_pipeline_does_not_use_network_when_models_unavailable(self):
        with patch.object(server.httpx,'Client',side_effect=AssertionError('Network forbidden')),patch.object(server.httpx,'AsyncClient',side_effect=AssertionError('Network forbidden')):
            key=self.client.post('/api/import/pdf',json=self.pdf()).json()['id'];m=self.wait(key)
            self.assertEqual(m['status'],'ready')
            result=self.client.get('/api/search',params={'q':'Pro price','library':'captures'}).json()
            self.assertEqual(result['mode'],'text');self.assertIn(key,result['ids'])

    def test_model_failure_does_not_erase_ocr_and_embeddings_can_be_added(self):
        with patch.object(server,'model_list',AsyncMock(return_value=[server.VISION_MODEL,server.EMBED_MODEL])),patch.object(server.httpx,'Client',side_effect=RuntimeError('Offline model failure')),patch.object(server,'embed',AsyncMock(return_value=[1.,0.])):
            key=self.client.post('/api/import/pdf',json=self.pdf()).json()['id'];m=self.wait(key)
            self.assertEqual(m['stages']['vision'],'failed');self.assertEqual(m['stages']['embedding'],'ready');self.assertIn('$49',m['ocr_text'])
            result=self.client.get('/api/search',params={'q':'subscription','library':'captures'}).json()
            self.assertEqual(result['mode'],'hybrid');self.assertIn(key,result['ids'])

    def test_date_timezone_constraints(self):
        now=datetime.fromisoformat('2026-10-23T12:00:00+05:00')
        filters=retrieval.constraints("Tuesday's PDF",'Asia/Karachi',[],now)
        self.assertEqual(str(filters['start']),'2026-10-20')
        self.assertTrue(retrieval.eligible({'date':'2026-10-19T20:00:00Z','source_kind':'pdf'},filters))
        self.assertFalse(retrieval.eligible({'date':'2026-10-20T20:00:00Z','source_kind':'pdf'},filters))
        self.assertEqual(self.client.get('/api/search',params={'tz':'Not/AZone'}).status_code,422)

    def test_no_match_and_samples_separated(self):
        self.assertEqual(self.client.get('/api/search',params={'q':'submarine unicorn','library':'captures'}).json()['ids'],[])
        self.assertEqual(self.client.get('/api/search',params={'q':'pricing','library':'captures'}).json()['ids'],[])

    def test_ocr_joined_words_and_adjacent_price_cell(self):
        self.assertEqual(retrieval.matches('Weeklyactiveusers',['weekly','active','users']),['weekly','active','users'])
        filters=retrieval.constraints('Pro price','UTC',[])
        item={'id':'table','title':'Price','regions':[{'id':'a','text':'Pro','box':[.1,.2,.2,.25]},{'id':'b','text':'$49','box':[.4,.2,.5,.25]}],'ocr_text':'Pro $49'}
        result=retrieval.rank([item],filters,[],{},None)
        self.assertIn('b',result[0]['region_ids'])


if __name__=='__main__':unittest.main()
