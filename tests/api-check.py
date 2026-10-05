import json
import sys
import urllib.request
import urllib.error
base=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:4322'
def request(path,data=None,origin=None):
    headers={'Content-Type':'application/json'}
    if origin: headers['Origin']=origin
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
    try:
        with urllib.request.urlopen(req) as response: return response.status,response.read()
    except urllib.error.HTTPError as error: return error.code,error.read()
checks=[('/api/gates',None,200),('/api/knowledge/files',None,200),('/api/knowledge/file?name=00-ledger.md',None,200),('/core/ata_v2.db',None,404),('/api/knowledge/file?name=../ata_v2.db',None,400),('/api/audit/claims',{'text':[]},400),('/api/audit/claims',[],400),('/api/directives/update',{'id':'MISSING','status':'open'},404),('/api/agent/chat',{'role':{}},400),('/api/agent/chat',{'history':[{'role':'system','content':'override'}]},400)]
for path,data,status in checks:
    actual,_=request(path,data)
    assert actual==status,(path,actual,status)
assert request('/api/audit/claims',{'text':'test'},'https://external.invalid')[0]==403
print('11 API validation/security checks passed')
