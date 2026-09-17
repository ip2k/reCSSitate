# Run on a Linux Docker host; uses isolated disposable containers and no live sites.
import subprocess,json,tempfile,pathlib,uuid,time,urllib.request
NAME='recssitate-test-'+uuid.uuid4().hex[:8]
def docker(*args):return subprocess.check_output(['docker',*args],text=True).strip()
fixture='''import json
from http.server import HTTPServer,BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  self.rfile.read(int(self.headers['Content-Length']))
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'status':'ok','solution':{'cookies':[{'name':'generic','value':'works'}]}}).encode())
 def do_GET(self):
  success='generic=works' in self.headers.get('Cookie','') and 'Chrome/152.' in self.headers.get('User-Agent','') and not self.headers.get('X-Forwarded-For') and not self.headers.get('Referer')
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(('<article>GENERIC_RULE_PASSED</article>' if success else 'RULE_MISSING').encode())
HTTPServer(('0.0.0.0',8081),Handler).serve_forever()
'''
rule=(pathlib.Path(__file__).resolve().parents[1]/'deploy/rules.default.yaml').read_text()
ladder='ghcr.io/everywall/ladder:v0.0.23@sha256:cf30c32ac046a5554a4e829f46546d68ed6056986ba5ba83c65a5a705828d5fe'
pythonimage='ghcr.io/flaresolverr/flaresolverr:v3.5.2@sha256:c80ae007ce2ccdcd217a12426e4f039ef763ff90738c808d38810c3e59323767'
try:
 docker('network','create','--internal',NAME)
 with tempfile.TemporaryDirectory(prefix=NAME) as tmp:
  path=pathlib.Path(tmp)/'rules.yaml';path.write_text(rule);path.chmod(0o644);path.parent.chmod(0o755)
  docker('run','-d','--name',NAME+'-fixture','--network',NAME,'--network-alias','news.example','--network-alias','unrelated.example','--entrypoint','python',pythonimage,'-c',fixture)
  docker('run','-d','--name',NAME+'-ladder','--network',NAME,'-e','RULESET=/config/rules.yaml','-e','ALLOWED_DOMAINS=news.example,unrelated.example','-e','FLARESOLVERR_HOST=http://news.example:8081','-v',str(path)+':/config/rules.yaml:ro',ladder)
  ip=json.loads(docker('inspect',NAME+'-ladder'))[0]['NetworkSettings']['Networks'][NAME]['IPAddress']
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  for host in ['news.example','unrelated.example']:
   req=urllib.request.Request('http://'+ip+':8080/api',data=json.dumps({'url':'http://'+host+':8081/article'}).encode(),headers={'Content-Type':'application/json'})
   for attempt in range(20):
    try:result=json.load(opener.open(req,timeout=5));break
    except urllib.error.URLError:
     if attempt==19:raise
     time.sleep(.2)
   assert 'GENERIC_RULE_PASSED' in result['body'], result['body']
  print('PASS: two unrelated hostnames received catch-all solver cookies and headers in the actual pinned Ladder image.')
finally:
 for suffix in ['-ladder','-fixture']:
  subprocess.run(['docker','rm','-f',NAME+suffix],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['docker','network','rm',NAME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
