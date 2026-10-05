"""CSS-only loopback302 baseline; no Django, app scripts, DB or credentials."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import threading
import sys

with_shared_motion='--with-shared-motion' in sys.argv

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/finish':
            self.send_response(200);self.end_headers();threading.Thread(target=self.server.shutdown,daemon=True).start();return
        if self.path=='/motion.js' and with_shared_motion:
            body=Path('/root/kidsmap-task33/static/js/motion.js').read_bytes();content='application/javascript'
        elif self.path=='/motion.css':
            body=Path('/root/kidsmap-task33/static/css/motion.css').read_bytes();content='text/css'
        else:
            name=self.path.strip('/')
            script='<script src="/motion.js" defer></script>'if with_shared_motion else''
            body=('<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/motion.css">'+script+'</head><body><header class="km-header">QA22 transition baseline</header><h1>'+name+'</h1><form method="post" action="'+('/b'if name=='a'else'/a')+'"><button>Submit synthetic form</button></form></body></html>').encode();content='text/html'
        self.send_response(200);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        if self.path in('/deny','/stale'):
            self.send_response(429 if self.path=='/deny'else 409);self.end_headers();return
        self.send_response(302);self.send_header('Location',self.path);self.end_headers()
    def log_message(self,*args):pass

server=ThreadingHTTPServer(('127.0.0.1',8783),Handler)
timer=threading.Timer(180,server.shutdown);timer.daemon=True;timer.start()
print('CSS-only loopback baseline ready',flush=True)
try:server.serve_forever(poll_interval=.2)
finally:timer.cancel();server.server_close()
