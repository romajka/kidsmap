from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, unquote
import mimetypes
root=Path(__file__).resolve().parents[4]
owner=root/'docs/task33/design'
assets={'/static/img/logo-mark.svg','/static/fonts/MaterialSymbolsRounded.woff2','/static/fonts/chiron/ChironGoRoundTC-PublicSubset.woff2'}
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  name=unquote(urlsplit(self.path).path)
  p=(root/name.lstrip('/')).resolve()
  if name not in assets and not (p.is_relative_to(owner) and p.suffix in {'.html','.css','.js','.png','.md','.json'}):
   self.send_error(404); return
  if not p.is_file(): self.send_error(404); return
  self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(p.name)[0] or 'application/octet-stream');self.end_headers();self.wfile.write(p.read_bytes())
 def log_message(self,*args): pass
HTTPServer(('127.0.0.1',8763),Handler).serve_forever()
