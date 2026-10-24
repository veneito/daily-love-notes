import contextlib,io,json,tempfile,threading,unittest
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import server

class AuthTests(unittest.TestCase):
    def test_permissions_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            server.DATA=Path(directory);server.SITE=Path('dist').resolve()
            output=io.StringIO()
            with contextlib.redirect_stdout(output):server.init()
            tokens={x['account']:parse_qs(urlsplit(x['setup_url']).fragment)['setup'][0] for x in map(json.loads,output.getvalue().splitlines())}
            http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);server.ORIGIN='http://127.0.0.1:'+str(http.server_port)
            thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            def request(method,path,data=None,cookie=None,origin=None):
                client=HTTPConnection('127.0.0.1',http.server_port)
                headers={'Origin':origin or server.ORIGIN,'Content-Type':'application/json'}
                if cookie:headers['Cookie']=cookie.split(';')[0]
                client.request(method,path,json.dumps(data) if data is not None else None,headers)
                response=client.getresponse();body=response.read();result=(response.status,json.loads(body) if 'application/json' in response.getheader('Content-Type','') else body,response.getheader('Set-Cookie'));client.close();return result
            try:
                self.assertEqual(request('GET','/api/today')[0],401)
                cookies={}
                for name in ['owner','reader']:
                    status,body,cookie=request('POST','/api/setup',{'token':tokens[name],'password':'a very cozy test password'})
                    self.assertEqual(status,200);self.assertIn('HttpOnly',cookie);self.assertIn('Secure',cookie);cookies[name]=cookie
                self.assertEqual(request('POST','/api/setup',{'token':tokens['owner'],'password':'a very cozy test password'})[0],400)
                self.assertEqual(request('GET','/api/notes',cookie=cookies['reader'])[0],403)
                status,body,_=request('GET','/api/today',cookie=cookies['reader']);self.assertEqual(status,200);self.assertEqual(set(body),{'note','date'})
                self.assertEqual(request('GET','/notes.js',cookie=cookies['owner'])[0],404)
                self.assertEqual(request('GET','/notes.js?v=365-1')[0],404)
                self.assertEqual(request('GET','/server.py')[0],404)
                self.assertEqual(request('PUT','/api/notes/1',{'text':'no','revision':1},cookies['reader'])[0],403)
                status,body,_=request('GET','/api/notes',cookie=cookies['owner']);self.assertEqual(len(body['notes']),365)
                status,body,_=request('PUT','/api/notes/1',{'text':'A changed note, kept safely.','revision':1},cookies['owner']);self.assertEqual(status,200);self.assertEqual(body['note']['revision'],2)
                self.assertEqual(request('PUT','/api/notes/1',{'text':'conflict','revision':1},cookies['owner'])[0],409)
                self.assertEqual(request('PUT','/api/notes/1',{'text':'bad origin','revision':2},cookies['owner'],'https://example.com')[0],400)
                self.assertEqual(request('POST','/api/widget-pair',{})[0],401)
                status,pair,_=request('POST','/api/widget-pair',{},cookies['reader']);self.assertEqual(status,200)
                status,widget,_=request('POST','/api/widget-connect',{'code':pair['code']});self.assertEqual(status,200)
                self.assertEqual(request('POST','/api/widget-connect',{'code':pair['code']})[0],400)
                def widget_get(path):
                    client=HTTPConnection('127.0.0.1',http.server_port);client.request('GET',path,headers={'Authorization':'Bearer '+widget['token']});r=client.getresponse();data=json.loads(r.read());client.close();return r.status,data
                status,daily=widget_get('/api/widget-today');self.assertEqual(status,200);self.assertEqual(set(daily['note']),{'day','text'})
                self.assertEqual(widget_get('/api/notes')[0],401)
                self.assertEqual(request('POST','/api/widget-disconnect',{},cookies['reader'])[0],200)
                self.assertEqual(widget_get('/api/widget-today')[0],401)
                self.assertEqual(request('GET','/manifest.webmanifest')[0],200)
                with server.db() as c:self.assertEqual(c.execute('SELECT text FROM notes WHERE day=1').fetchone()[0],'A changed note, kept safely.')
                self.assertEqual(request('POST','/api/logout',{},cookies['owner'])[0],200)
                self.assertEqual(request('GET','/api/notes',cookie=cookies['owner'])[0],401)
                self.assertEqual(request('POST','/api/login',{'name':'owner','password':'wrong'})[0],401)
                self.assertEqual(request('POST','/api/login',{'name':'owner','password':'a very cozy test password'})[0],200)
            finally:http.shutdown();http.server_close()

if __name__=='__main__':unittest.main()
