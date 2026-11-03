"""Integration tests call the actual WSGI API, including session cookies and SQLite."""
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import School, money, day, password_matches

class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.app=School(cls.temp.name, seed_demo=True)
        cls.pw='Local-test-only-123456'

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def api(cls,path,body=None,cookie='',**overrides):
        path,_,query=path.partition('?')
        raw=json.dumps(body or {},ensure_ascii=False).encode()
        env={'REQUEST_METHOD':'POST' if body is not None else 'GET','PATH_INFO':path,'QUERY_STRING':query,'HTTP_HOST':'localhost:8765','HTTP_ORIGIN':'http://localhost:8765','HTTP_COOKIE':cookie,'REMOTE_ADDR':'127.0.0.1','CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(raw)),'HTTP_X_SCHOOL_ERP':'1','wsgi.input':io.BytesIO(raw)}
        env.update(overrides)
        captured={}
        def response(status,headers):
            captured.update(status=int(status.split()[0]),headers=dict(headers))
        data=b''.join(cls.app(env,response))
        parsed=json.loads(data) if captured['headers'].get('Content-Type','').startswith('application/json') else data
        cookie=captured['headers'].get('Set-Cookie','').split(';')[0]
        return captured['status'],parsed,cookie,captured['headers']

    @classmethod
    def login(cls,username):
        code,data,cookie,_=cls.api('/api/auth',{'action':'login','username':username,'password':cls.pw})
        assert code==200,(code,data)
        return cookie

    @classmethod
    def invite(cls,role,**values):
        status,result,_,_=cls.api('/api/access',{'action':'invite','role':role,'label':'test invite',**values},cls.manager)
        assert status==200,(status,result)
        return result['token']

    @classmethod
    def register(cls,name,token):
        status,result,cookie,headers=cls.api('/api/auth',{'action':'register','name':name,'username':name,'password':cls.pw,'token':token,'role':'manager'})
        assert status==200,(status,result)
        return cookie

    def test_01_first_run_and_auth(self):
        self.assertEqual(self.api('/api/school')[0],401)
        self.assertTrue(self.api('/api/access')[1]['setupRequired'])
        status,result,cookie,headers=self.api('/api/auth',{'action':'setup','username':'admin','name':'Test manager','password':self.pw})
        self.assertEqual(status,200,result)
        Integration.manager=cookie
        self.assertIn('HttpOnly',headers['Set-Cookie'])
        self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        self.assertNotIn(self.pw,headers['Set-Cookie'])
        self.assertEqual(self.api('/api/auth',{'action':'setup','username':'admin2','name':'Bad','password':self.pw})[0],409)
        self.assertEqual(self.api('/api/auth',{'action':'login','username':'admin','password':'wrong-but-long-enough'})[0],401)
        with self.app.connection() as db:
            h=db.execute('SELECT password_hash FROM local_users').fetchone()[0]
            self.assertNotIn(self.pw,h)
            self.assertTrue(password_matches(self.pw,h))
        self.assertEqual(self.api('/dashboard')[0],302)
        self.assertEqual(self.api('/data/school.sqlite3',cookie=cookie)[0],404)
        self.assertEqual(self.api('/schema.sql',cookie=cookie)[0],404)
        for kwargs in [{'HTTP_ORIGIN':'https://evil.example'},{'HTTP_HOST':'evil.example'},{'HTTP_X_SCHOOL_ERP':''},{'CONTENT_LENGTH':'16001'}]:
            self.assertIn(self.api('/api/access',{'action':'invite'},cookie,**kwargs)[0],(403,413))

    def test_02_financial_transaction_and_race(self):
        status,d,_,_=self.api('/api/school',cookie=self.manager)
        self.assertEqual(status,200)
        self.assertEqual(len(d['students']),6)
        self.assertEqual(sum(i['amount'] for i in d['invoices']),2460000000)
        sid=d['students'][0]['id']
        Integration.sid=sid
        Integration.parent_sid=d['students'][1]['id']
        Integration.classb_sid=d['students'][3]['id']
        invoice={'action':'invoice','studentId':sid,'title':'QA fee','dueDate':'2026-11-02','amount':'۲۰۰۰۰۰۰','eventKey':'fee-dedup'}
        status,d,_,_=self.api('/api/school',invoice,self.manager)
        self.assertEqual(status,200,d)
        Integration.invoice=d['id']
        self.assertTrue(self.api('/api/school',invoice,self.manager)[1]['repeated'])
        self.assertEqual(self.api('/api/school',{**invoice,'amount':'3000000'},self.manager)[0],409)
        receipt={'action':'receipt','invoiceId':self.invoice,'amount':'500000','eventKey':'receipt-dedup','reference':'QA'}
        self.assertEqual(self.api('/api/school',receipt,self.manager)[0],200)
        self.assertTrue(self.api('/api/school',receipt,self.manager)[1]['repeated'])
        self.assertEqual(self.api('/api/school',{**receipt,'amount':'1600000','eventKey':'excess'},self.manager)[0],409)
        with ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(self.api,'/api/school',{**receipt,'amount':'1000000','eventKey':f'race-{i}'},self.manager) for i in range(2)]
            self.assertEqual(sorted(f.result()[0] for f in futures),[200,409])
        with self.app.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM receipts WHERE invoice_id=?',(self.invoice,)).fetchone()[0],2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM journals WHERE event_id=?',(self.invoice,)).fetchone()[0],1)
            self.assertEqual(db.execute('SELECT SUM(amount) FROM receipts WHERE invoice_id=?',(self.invoice,)).fetchone()[0],15000000)
        self.assertEqual(self.api('/api/school',{**invoice,'studentId':'other-school-student','eventKey':'foreign'},self.manager)[0],404)
        self.assertEqual(money('۱٬۲۳۴'),12340)
        for amount in ('-1','0','1.2','NaN','1000000001'):
            with self.assertRaises(Exception):money(amount)
        with self.assertRaises(Exception):day('2026-02-31')

    def test_03_real_accounts_scopes_and_role_forgery(self):
        Integration.teacher=self.register('teacher',self.invite('teacher',className='پنجم ب'))
        Integration.parent=self.register('parent',self.invite('parent',studentId=self.parent_sid))
        Integration.accountant=self.register('accountant',self.invite('accountant'))
        teacher=self.api('/api/school',cookie=self.teacher)[1]
        self.assertEqual(teacher['role'],'teacher')
        self.assertEqual(len(teacher['students']),3)
        self.assertTrue(all(s['class_name']=='پنجم ب' for s in teacher['students']))
        self.assertEqual(teacher['invoices'],[])
        self.assertEqual(teacher['journals'],[])
        self.assertEqual(self.api('/api/school?role=manager',cookie=self.teacher)[0],403)
        self.assertEqual(self.api('/api/school',{'action':'student','role':'manager'},self.teacher)[0],403)
        self.assertEqual(self.api('/api/access?manage=1',cookie=self.teacher)[0],403)
        self.assertEqual(self.api('/api/school',{'action':'invoice'},self.teacher)[0],403)
        attendance={'action':'attendance','studentId':self.sid,'day':'2026-11-02','status':'present'}
        self.assertEqual(self.api('/api/school',attendance,self.teacher)[0],403)
        self.assertEqual(self.api('/api/school',{**attendance,'studentId':self.classb_sid},self.teacher)[0],200)
        parent=self.api('/api/school',cookie=self.parent)[1]
        self.assertEqual([s['id'] for s in parent['students']],[self.parent_sid])
        self.assertEqual(len(parent['invoices']),1)
        self.assertEqual(parent['journals'],[])
        self.assertEqual(self.api('/api/school',attendance,self.parent)[0],403)
        accountant=self.api('/api/school',cookie=self.accountant)[1]
        self.assertGreater(len(accountant['journals']),0)
        self.assertEqual(accountant['attendance'],[])
        self.assertEqual(self.api('/api/school',{'action':'student'},self.accountant)[0],403)

    def test_04_invitation_race_revocation_and_expiry(self):
        token=self.invite('accountant')
        with ThreadPoolExecutor(2) as pool:
            results=list(pool.map(lambda name:self.api('/api/auth',{'action':'register','name':name,'username':name,'password':self.pw,'token':token}),['raceusera','raceuserb']))
        self.assertEqual(sorted(r[0] for r in results),[200,409])
        code=self.invite('accountant')
        with self.app.connection() as db:
            from server import digest
            ident=db.execute('SELECT id FROM invitations WHERE token_hash=?',(digest(code),)).fetchone()[0]
        self.assertEqual(self.api('/api/access',{'action':'revokeInvite','id':ident},self.manager)[0],200)
        self.assertEqual(self.api('/api/auth',{'action':'register','username':'revoked','name':'Revoked','password':self.pw,'token':code})[0],409)
        expired=self.invite('accountant')
        with self.app.connection() as db:
            db.execute('UPDATE invitations SET expires_at=? WHERE token_hash=?',('2000-01-01T00:00:00.000Z',digest(expired)))
        self.assertEqual(self.api('/api/auth',{'action':'register','username':'expired','name':'Expired','password':self.pw,'token':expired})[0],409)
        members=self.api('/api/access?manage=1',cookie=self.manager)[1]
        self.assertNotIn('token_hash',json.dumps(members))
        self.assertNotIn('password_hash',json.dumps(members))

    def test_05_backup_restore_and_persistence(self):
        self.assertEqual(self.api('/api/backup')[0],401)
        self.assertEqual(self.api('/api/backup',cookie=self.teacher)[0],403)
        status,data,_,headers=self.api('/api/backup',cookie=self.manager)
        self.assertEqual(status,200)
        self.assertTrue(data.startswith(b'SQLite format 3'))
        restored=Path(self.temp.name)/'restored.sqlite3'
        restored.write_bytes(data)
        with sqlite3.connect(restored) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM students').fetchone()[0],6)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM local_users').fetchone()[0],5)
        restarted=School(self.temp.name)
        self.assertEqual(restarted.db_path,self.app.db_path)
        self.assertFalse(self.api('/api/access')[1]['setupRequired'])

    def test_055_hosted_setup_protection(self):
        import io
        with tempfile.TemporaryDirectory() as directory:
            app=School(directory,secure_cookie=True,setup_token='local-test-setup-token')
            def setup(token):
                raw=json.dumps({'action':'setup','username':'hostadmin','name':'Host admin','password':self.pw,'setupToken':token}).encode()
                env={'REQUEST_METHOD':'POST','PATH_INFO':'/api/auth','QUERY_STRING':'','HTTP_HOST':'localhost:8765','HTTP_ORIGIN':'https://localhost:8765','CONTENT_TYPE':'application/json','HTTP_X_SCHOOL_ERP':'1','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw)}
                captured={}
                result=b''.join(app(env,lambda status,headers:captured.update(status=int(status.split()[0]),headers=dict(headers))))
                return captured,result
            self.assertEqual(setup('wrong')[0]['status'],403)
            response,_=setup('local-test-setup-token')
            self.assertEqual(response['status'],200)
            self.assertIn('; Secure',response['headers']['Set-Cookie'])

    def test_06_suspension_logout_and_limits(self):
        members=self.api('/api/access?manage=1',cookie=self.manager)[1]['members']
        teacher=next(m for m in members if m['role']=='teacher')
        owner=next(m for m in members if m['role']=='manager')
        self.assertEqual(self.api('/api/access',{'action':'memberStatus','userId':owner['user_id'],'status':'disabled'},self.manager)[0],403)
        self.assertEqual(self.api('/api/access',{'action':'memberStatus','userId':teacher['user_id'],'status':'disabled'},self.manager)[0],200)
        self.assertEqual(self.api('/api/school',cookie=self.teacher)[0],401)
        self.assertEqual(self.api('/api/auth',{'action':'login','username':'teacher','password':self.pw})[0],403)
        self.assertEqual(self.api('/api/access',{'action':'memberStatus','userId':teacher['user_id'],'status':'active'},self.manager)[0],200)
        teacher_cookie=self.login('teacher')
        self.assertEqual(self.api('/api/auth',{'action':'logout'},teacher_cookie)[0],200)
        self.assertEqual(self.api('/api/school',cookie=teacher_cookie)[0],401)
        for i in range(10):
            self.assertEqual(self.api('/api/auth',{'action':'login','username':'admin','password':'wrong-but-long-enough'},REMOTE_ADDR='test-limiter')[0],401)
        self.assertEqual(self.api('/api/auth',{'action':'login','username':'admin','password':self.pw},REMOTE_ADDR='test-limiter')[0],429)

if __name__=='__main__':
    unittest.main(verbosity=2)
