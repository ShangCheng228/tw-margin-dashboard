import json, pathlib, datetime, urllib.request
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
now=datetime.datetime.now(ZoneInfo('Asia/Taipei'))
date=now.strftime('%Y%m%d')
urls={'margin':f'https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date={date}&selectType=MS','index':f'https://www.twse.com.tw/exchangeReport/FMTQIK?response=json&date={date}'}
results={}; errors={}
for key,url in urls.items():
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
  with urllib.request.urlopen(req,timeout=25) as resp: payload=json.load(resp)
  if not isinstance(payload,dict) or payload.get('stat') not in (None,'OK') or not (payload.get('data') or payload.get('tables')): raise ValueError('No verified data')
  results[key]=payload
 except Exception as e: errors[key]=str(e)
if not results: raise SystemExit('No official source returned usable data: '+str(errors))
archive=ROOT/'data'/'raw';archive.mkdir(parents=True,exist_ok=True)
for k,payload in results.items(): (archive/f'{date}_{k}.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
(ROOT/'data'/'status.json').write_text(json.dumps({'checked_at':now.isoformat(),'available':list(results),'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved',list(results),'errors',errors)
