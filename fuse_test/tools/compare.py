"""Strict comparison; masks are supplied by the original suite only."""
import itertools

def compare_record(c,e,tr,d):
 errors=[]
 codeaddr={((c['initial']['PC']+i)&0xffffff) if c['initial']['ADL'] else (c['initial']['MBASE']<<16)|((c['initial']['PC']+i)&65535) for i in range(len(c['code']))}
 if any(ev['kind']=='MR' and ev['address'] in codeaddr for ev in tr['events']):errors.append(dict(kind='TRACE_CODE_DATA_ALIAS_UNSUPPORTED'))
 if d['status']:errors.append(dict(kind='FRAME_FAULT' if d['status']==2 else 'TIMEOUT',cycles=d['cycles']))
 for k,v in e['state'].items():
  mask=c['mask'].get(k,0xffffff);got=d['state'][k]
  if mask and (got is None or (got^v)&mask):errors.append(dict(kind='register',register=k,expected=v,actual=got,mask=mask))
 for addr,v in e['memory'].items():
  got=d['memory'].get(addr)
  if got!=v:errors.append(dict(kind='memory',address=addr,expected=v,actual=got))
 if d['events']!=tr['events']:
  first=next((i for i,(x,y) in enumerate(itertools.zip_longest(d['events'],tr['events'])) if x!=y),None)
  errors.append(dict(kind='events',first_difference=first,expected=tr['events'][first] if first<len(tr['events']) else None,actual=d['events'][first] if first<len(d['events']) else None,expected_count=len(tr['events']),actual_count=len(d['events'])))
 arch_errors=[e for e in errors if e['kind'] not in ['events','TRACE_CODE_DATA_ALIAS_UNSUPPORTED']]
 return dict(id=c['id'],instruction=c['instruction'],coverage=c['coverage'],passed=not errors,architectural_passed=not arch_errors,event_stream_passed=not any(e['kind'] in ['events','TRACE_CODE_DATA_ALIAS_UNSUPPORTED'] for e in errors),status=d['status'],cycles=d['cycles'],errors=errors)
