import socket
import socketserver
import select
import subprocess

target = subprocess.check_output(['docker','inspect','m09s10-fix-r1-app','--format',
    '{{with index .NetworkSettings.Networks "m09full-r1-net"}}{{.IPAddress}}{{end}}'], text=True).strip()
assert target.startswith('172.')
class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection((target,8000),timeout=15) as remote:
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
with Server(('127.0.0.1',33400),Handler) as server:
    print('Own isolated SOCIAL07 proxy loopback33400 ready',flush=True)
    server.serve_forever()
