import socket
import socketserver
import select
import subprocess

import sys
port=int(sys.argv[1]) if len(sys.argv)>1 else 33610
remote_port=8000
target = subprocess.check_output(['docker','inspect','m10s22-fix-r1-app','--format',
    '{{with index .NetworkSettings.Networks "m09full-r1-net"}}{{.IPAddress}}{{end}}'], text=True).strip()
assert target.startswith('172.')
class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection((target,remote_port),timeout=15) as remote:
            while True:
                readable,_,_ = select.select([self.request,remote],[],[],30)
                if not readable:
                    return
                for source in readable:
                    data = source.recv(65536)
                    if not data:
                        return
                    (remote if source is self.request else self.request).sendall(data)
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
with Server(('127.0.0.1',port),Handler) as server:
    print('Own isolated SITE19 proxy loopback33610 ready',flush=True)
    server.serve_forever()
