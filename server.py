import hashlib, hmac, json, os, secrets, sqlite3, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit
from contextlib import contextmanager

DATA=Path(os.environ.get('LOVE_DATA','data'))
SITE=Path(os.environ.get('LOVE_SITE','dist'))
ORIGIN=os.environ.get('PUBLIC_ORIGIN','https://notes.example.com').rstrip('/')
COOKIE='__Host-love'
@contextmanager
def db():
    c=sqlite3.connect(DATA/'love.sqlite',timeout=15); c.row_factory=sqlite3.Row
    try:
        with c:yield c
    finally:c.close()
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def password_hash(value,salt): return hashlib.scrypt(value.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1,maxmem=64*1024*1024).hex()
def init():
    DATA.mkdir(parents=True,exist_ok=True)
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS users(name TEXT PRIMARY KEY,role TEXT NOT NULL,salt TEXT,password TEXT,setup TEXT,setup_expires INTEGER);
        CREATE TABLE IF NOT EXISTS notes(day INTEGER PRIMARY KEY,text TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,name TEXT NOT NULL,expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY,count INTEGER NOT NULL,until INTEGER NOT NULL);''')
        c.executescript('''CREATE TABLE IF NOT EXISTS widget_pairs(code TEXT PRIMARY KEY,name TEXT NOT NULL,expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS widgets(token TEXT PRIMARY KEY,name TEXT NOT NULL,expires INTEGER NOT NULL);''')
        if c.execute('SELECT count(*) FROM notes').fetchone()[0]==0:
            source=(SITE/'notes.js').read_text(encoding='utf-8'); notes=json.loads(source[source.index('=')+1:].strip().rstrip(';'))
            assert len(notes)==365
            c.executemany('INSERT INTO notes(day,text) VALUES(?,?)',enumerate(notes,1))
        for name,role in [(os.environ.get('ADMIN_USERNAME','owner'),'admin'),(os.environ.get('READER_USERNAME','reader'),'reader')]:
            if not c.execute('SELECT 1 FROM users WHERE name=?',(name,)).fetchone():
                token=secrets.token_urlsafe(32)
                c.execute('INSERT INTO users(name,role,setup,setup_expires) VALUES(?,?,?,?)',(name,role,digest(token),int(time.time())+86400))
                print(json.dumps({'account':name,'setup_url':ORIGIN+'/#setup='+token}),flush=True)
def today():
    from datetime import datetime,date
    from zoneinfo import ZoneInfo
    now=datetime.now(ZoneInfo(os.environ.get('APP_TIMEZONE','UTC')))
    return ((now.date()-date.fromisoformat(os.environ.get('START_DATE','2026-01-01'))).days%365)+1,now.strftime('%B %d').replace(' 0',' ')

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def respond(self,status,payload,cookie=None):
        body=json.dumps(payload).encode(); self.send_response(status); self.headers_common()
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(body)
    def headers_common(self):
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
    def user(self):
        try:
            cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''));token=cookies[COOKIE].value
            with db() as c:return c.execute('SELECT u.name,u.role FROM users u JOIN sessions s ON u.name=s.name WHERE s.token=? AND s.expires>?',(digest(token),int(time.time()))).fetchone()
        except (KeyError,ValueError):return None
    def session(self,name):
        token=secrets.token_urlsafe(32)
        with db() as c:
            c.execute('DELETE FROM sessions WHERE expires<?',(int(time.time()),));c.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(token),name,int(time.time())+7*86400))
        return f'{COOKIE}={token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=604800'
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith('/api/'):
            if path=='/api/widget-today':
                auth=self.headers.get('Authorization','')
                with db() as c:
                    widget=c.execute('SELECT name FROM widgets WHERE token=? AND expires>?',(digest(auth.removeprefix('Bearer ')),int(time.time()))).fetchone() if auth.startswith('Bearer ') else None
                    if not widget:return self.respond(401,{'error':'Reconnect your widget in the app.'})
                    day,date=today();note=dict(c.execute('SELECT day,text FROM notes WHERE day=?',(day,)).fetchone())
                return self.respond(200,{'note':note,'date':date,'url':ORIGIN})
            user=self.user()
            if path=='/api/me':return self.respond(200,{'user':dict(user) if user else None})
            if not user:return self.respond(401,{'error':'Please sign in.'})
            day,date=today()
            with db() as c:
                if path=='/api/today':return self.respond(200,{'note':dict(c.execute('SELECT * FROM notes WHERE day=?',(day,)).fetchone()),'date':date})
                if path=='/api/notes':
                    if user['role']!='admin':return self.respond(403,{'error':'Only Owner can browse and edit the collection.'})
                    return self.respond(200,{'notes':[dict(n) for n in c.execute('SELECT * FROM notes ORDER BY day')]})
            return self.respond(404,{'error':'Not found.'})
        name='index.html' if path=='/' else path.lstrip('/')
        allowed={'index.html':'text/html','style.css':'text/css','intro.css':'text/css','motion.css':'text/css','auth.css':'text/css','app.js':'text/javascript','intro.js':'text/javascript','motion.js':'text/javascript','manifest.webmanifest':'application/manifest+json','sw.js':'text/javascript','pwa.js':'text/javascript','pwa.css':'text/css','icon-192.png':'image/png','icon-512.png':'image/png','apple-touch-icon.png':'image/png','love-widget.js':'text/javascript','love-widget.apk':'application/vnd.android.package-archive'}
        if name not in allowed:return self.respond(404,{'error':'Not found.'})
        try: body=(SITE/name).read_bytes()
        except OSError:return self.respond(404,{'error':'Not found.'})
        self.send_response(200);self.headers_common();self.send_header('Content-Type',allowed[name]+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def body(self):
        if self.headers.get('Origin')!=ORIGIN and not (urlsplit(self.path).path=='/api/widget-connect' and not self.headers.get('Origin')):raise ValueError('Please use the website to make this change.')
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Expected JSON.')
        length=int(self.headers.get('Content-Length','0'))
        if length<1 or length>8192:raise ValueError('Request is too large.')
        result=json.loads(self.rfile.read(length))
        if not isinstance(result,dict):raise ValueError('Invalid request.')
        return result
    def throttle(self,key):
        now=int(time.time())
        with db() as c:
            c.execute('DELETE FROM attempts WHERE until<?',(now,))
            row=c.execute('SELECT count FROM attempts WHERE key=?',(key,)).fetchone()
            if row and row['count']>=12:return False
            c.execute('INSERT INTO attempts VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1',(key,now+900))
        return True
    def do_POST(self):
        try:data=self.body()
        except (ValueError,json.JSONDecodeError):return self.respond(400,{'error':'Invalid request. Please reload and try again.'})
        path=urlsplit(self.path).path
        if path=='/api/widget-connect':
            ip=self.headers.get('CF-Connecting-IP',self.client_address[0])
            if not self.throttle('widget:'+ip):return self.respond(429,{'error':'Too many attempts. Try again in 15 minutes.'})
            code=data.get('code','')
            if not isinstance(code,str):return self.respond(400,{'error':'Enter your pairing code.'})
            with db() as c:
                c.execute('DELETE FROM widget_pairs WHERE expires<?',(int(time.time()),))
                pair=c.execute('SELECT name FROM widget_pairs WHERE code=?',(digest(code.strip().upper()),)).fetchone()
                if not pair:return self.respond(400,{'error':'That pairing code expired or was already used. Create another in the app.'})
                changed=c.execute('DELETE FROM widget_pairs WHERE code=?',(digest(code.strip().upper()),)).rowcount
                if changed!=1:return self.respond(400,{'error':'Create a new pairing code.'})
                token=secrets.token_urlsafe(32);c.execute('INSERT INTO widgets VALUES(?,?,?)',(digest(token),pair['name'],int(time.time())+365*86400))
            return self.respond(200,{'token':token})
        if path in ('/api/widget-pair','/api/widget-disconnect'):
            user=self.user()
            if not user:return self.respond(401,{'error':'Please sign in.'})
            with db() as c:
                if path=='/api/widget-disconnect':
                    c.execute('DELETE FROM widgets WHERE name=?',(user['name'],));c.execute('DELETE FROM widget_pairs WHERE name=?',(user['name'],))
                    return self.respond(200,{'ok':True})
                code=secrets.token_hex(6).upper();c.execute('DELETE FROM widget_pairs WHERE name=?',(user['name'],));c.execute('INSERT INTO widget_pairs VALUES(?,?,?)',(digest(code),user['name'],int(time.time())+900))
            return self.respond(200,{'code':code,'expiresIn':900})
        if path in ('/api/login','/api/setup'):
            ip=self.headers.get('CF-Connecting-IP',self.client_address[0])
            if not self.throttle('ip:'+ip):return self.respond(429,{'error':'Too many attempts. Try again in 15 minutes.'})
            if path=='/api/setup':
                token=data.get('token','');password=data.get('password','')
                if not isinstance(token,str) or not isinstance(password,str) or not 12<=len(password)<=128:return self.respond(400,{'error':'Use a password between 12 and 128 characters.'})
                with db() as c:
                    user=c.execute('SELECT name,role FROM users WHERE setup=? AND setup_expires>? AND password IS NULL',(digest(token),int(time.time()))).fetchone()
                    if not user:return self.respond(400,{'error':'This setup link has expired or has already been used.'})
                    salt=secrets.token_hex(16);hashed=password_hash(password,salt)
                    changed=c.execute('UPDATE users SET salt=?,password=?,setup=NULL,setup_expires=NULL WHERE name=? AND password IS NULL',(salt,hashed,user['name'])).rowcount
                    if changed!=1:return self.respond(400,{'error':'This setup link has already been used.'})
                return self.respond(200,{'user':dict(user)},self.session(user['name']))
            name=data.get('name','');password=data.get('password','')
            if not isinstance(name,str) or not isinstance(password,str) or len(password)>128:return self.respond(401,{'error':'That username or password isn’t right.'})
            name=name.strip().lower()
            if not self.throttle('user:'+name):return self.respond(429,{'error':'Too many attempts. Try again in 15 minutes.'})
            with db() as c:user=c.execute('SELECT * FROM users WHERE name=?',(name,)).fetchone()
            actual=password_hash(password,user['salt'] if user and user['salt'] else '00'*16)
            if not user or not user['password'] or not hmac.compare_digest(actual,user['password']):return self.respond(401,{'error':'That username or password isn’t right.'})
            return self.respond(200,{'user':{'name':user['name'],'role':user['role']}},self.session(name))
        if path=='/api/logout':
            try:
                cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''))
                with db() as c:c.execute('DELETE FROM sessions WHERE token=?',(digest(cookies[COOKIE].value),))
            except (KeyError,ValueError):pass
            return self.respond(200,{'ok':True},f'{COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0')
        return self.respond(404,{'error':'Not found.'})
    def do_PUT(self):
        user=self.user()
        if not user:return self.respond(401,{'error':'Please sign in.'})
        if user['role']!='admin':return self.respond(403,{'error':'Only Owner can edit notes.'})
        try:
            data=self.body();day=int(urlsplit(self.path).path.removeprefix('/api/notes/'));text=data.get('text');revision=data.get('revision')
            if not urlsplit(self.path).path.startswith('/api/notes/') or not 1<=day<=365 or not isinstance(text,str) or not 1<=len(text.strip())<=2000 or type(revision)!=int:raise ValueError()
        except (ValueError,TypeError):return self.respond(400,{'error':'Write a note between 1 and 2,000 characters.'})
        with db() as c:
            if c.execute('UPDATE notes SET text=?,revision=revision+1 WHERE day=? AND revision=?',(text.strip(),day,revision)).rowcount!=1:return self.respond(409,{'error':'This note changed in another tab. Reload before editing it again.'})
            note=dict(c.execute('SELECT * FROM notes WHERE day=?',(day,)).fetchone())
        return self.respond(200,{'note':note})

if __name__=='__main__':
    import sys
    if '--renew-setup' in sys.argv:
        import contextlib,io
        with contextlib.redirect_stdout(io.StringIO()):init()
        with db() as c:
            for user in c.execute('SELECT name FROM users WHERE password IS NULL').fetchall():
                token=secrets.token_urlsafe(32);c.execute('UPDATE users SET setup=?,setup_expires=? WHERE name=?',(digest(token),int(time.time())+86400,user['name']))
                print(json.dumps({'account':user['name'],'setup_url':ORIGIN+'/#setup='+token}),flush=True)
    else:
        init()
        if '--init' not in sys.argv:ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','8080'))),Handler).serve_forever()
