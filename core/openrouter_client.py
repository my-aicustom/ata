"""OpenRouter client for text, vision, and thesis voice-note transcription."""
from __future__ import annotations
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

CHAT_URL = 'https://openrouter.ai/api/v1/chat/completions'
TRANSCRIPTION_URL = 'https://openrouter.ai/api/v1/audio/transcriptions'
DEFAULT = {
    # Thesis data may contain internal/confidential material. Do not default to :free endpoints.
    'fast': ['google/gemini-3.1-flash-lite'],
    'prose': ['google/gemini-3.1-flash-lite','google/gemini-3.7-flash'],
    'reasoning': ['google/gemini-3.7-flash','google/gemini-3.1-flash-lite'],
}
DEFAULT_VISION = ['google/gemini-3.1-flash-lite','google/gemini-3.7-flash']


def _env_models(tier: str) -> List[str]:
    raw=os.getenv('ATA_MODELS_'+tier.upper(),'').strip()
    return [x.strip() for x in raw.split(',') if x.strip()] or DEFAULT.get(tier,DEFAULT['fast'])


def _audio_format(filename: str) -> str:
    ext=(filename.rsplit('.',1)[-1] if '.' in filename else '').lower()
    aliases={'mpeg':'mp3','mpga':'mp3','oga':'ogg'}
    ext=aliases.get(ext,ext)
    allowed={'wav','mp3','m4a','ogg','aac','flac','webm','mp4'}
    if ext not in allowed:
        raise ValueError('Format audio tidak didukung untuk transkripsi: '+(ext or 'tanpa ekstensi'))
    return ext


class OpenRouterClient:
    def __init__(self, api_key: Optional[str]=None):
        self.api_key=api_key
    def get_key(self):
        if self.api_key is not None:
            return self.api_key
        return os.getenv('OPENROUTER_API_KEY','')
    def _headers(self, key: str) -> Dict[str,str]:
        return {'Authorization':'Bearer '+key,'Content-Type':'application/json','X-Title':'ATA v3 Thesis OS'}
    def _post_json(self, url: str, payload: Dict[str,Any], timeout: int=60) -> Dict[str,Any]:
        key=self.get_key()
        if not key: return {'success':False,'error':'OPENROUTER_API_KEY belum dikonfigurasi','content':''}
        req=urllib.request.Request(url,data=json.dumps(payload).encode('utf-8'),headers=self._headers(key))
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                data=json.loads(r.read().decode('utf-8'))
            return {'success':True,'data':data}
        except urllib.error.HTTPError as e:
            try: detail=e.read().decode('utf-8')[:1200]
            except Exception: detail=str(e)
            return {'success':False,'error':f'OpenRouter HTTP {e.code}: {detail}','content':''}
        except Exception as e:
            return {'success':False,'error':str(e),'content':''}

    def chat(self,messages:List[Dict[str,Any]],model:Optional[str]=None,temperature:float=.35,max_tokens:Optional[int]=None,tier:str='fast')->Dict[str,Any]:
        if not self.get_key(): return {'success':False,'error':'OPENROUTER_API_KEY belum dikonfigurasi','content':''}
        limit=max_tokens or int(os.getenv('ATA_MAX_TOKENS','4096'))
        last=''
        models_to_try = [model] if model else _env_models(tier)
        for m in models_to_try:
            result=self._post_json(CHAT_URL,{'model':m,'messages':messages,'temperature':temperature,'max_tokens':limit},timeout=60)
            if not result.get('success'):
                err=str(result.get('error',''))
                if 'can only afford' in err:
                    import re
                    m_afford = re.search(r'can only afford (\d+)', err)
                    if m_afford:
                        reduced = max(80, int(m_afford.group(1)) - 10)
                        retry_res = self._post_json(CHAT_URL,{'model':m,'messages':messages,'temperature':temperature,'max_tokens':reduced},timeout=45)
                        if retry_res.get('success'):
                            result = retry_res
            if not result.get('success'):
                last=result.get('error',''); continue
            data=result['data']; content=((data.get('choices') or [{}])[0].get('message') or {}).get('content','')
            if isinstance(content,list):
                content='\n'.join(str(x.get('text','')) for x in content if isinstance(x,dict) and x.get('type')=='text')
            if len(str(content).strip())<8:
                last='empty response'; continue
            return {'success':True,'model':data.get('model',m),'content':str(content),'raw':data}
        if not model:
            fallbacks=['nvidia/nemotron-3.5-lightning:free','liquid/lfm-2.5-2.6b:free']
            for fm in fallbacks:
                res=self._post_json(CHAT_URL,{'model':fm,'messages':messages,'temperature':temperature,'max_tokens':min(limit,2048)},timeout=40)
                if not res.get('success'): continue
                data=res['data']; content=((data.get('choices') or [{}])[0].get('message') or {}).get('content','')
                if isinstance(content,list):
                    content='\n'.join(str(x.get('text','')) for x in content if isinstance(x,dict) and x.get('type')=='text')
                if len(str(content).strip())>=8:
                    return {'success':True,'model':data.get('model',fm),'content':str(content),'raw':data}
        return {'success':False,'error':last or 'Semua model gagal','content':''}

    def transcribe(self, audio_bytes: bytes, filename: str, language: str='id', model: Optional[str]=None) -> Dict[str,Any]:
        if not self.get_key(): return {'success':False,'error':'OPENROUTER_API_KEY belum dikonfigurasi','text':''}
        try: fmt=_audio_format(filename)
        except ValueError as e: return {'success':False,'error':str(e),'text':''}
        payload={
            'model': model or os.getenv('ATA_TRANSCRIPTION_MODEL','openai/whisper-large-v3'),
            'input_audio': {'data':base64.b64encode(audio_bytes).decode('ascii'),'format':fmt},
            'response_format':'verbose_json',
        }
        if language: payload['language']=language
        result=self._post_json(TRANSCRIPTION_URL,payload,timeout=int(os.getenv('ATA_MEDIA_TIMEOUT','75')))
        if not result.get('success'):
            error=result.get('error','Transkripsi gagal')
            if 'timed out' in error.lower() or 'timeout' in error.lower():
                error += ' — upstream STT dapat timeout sekitar 60 detik; kompres atau pecah rekaman panjang, atau jalankan media worker di VPS.'
            return {'success':False,'error':error,'text':''}
        data=result['data']; text=str(data.get('text') or '').strip()
        if not text: return {'success':False,'error':'Provider transkripsi tidak mengembalikan teks','text':'','raw':data}
        return {'success':True,'text':text,'model':data.get('model',payload['model']),'usage':data.get('usage') or {},'segments':data.get('segments') or [],'raw':data}

    def vision(self, image_bytes: bytes, mime_type: str, prompt: str, model: Optional[str]=None) -> Dict[str,Any]:
        if not self.get_key(): return {'success':False,'error':'OPENROUTER_API_KEY belum dikonfigurasi','content':''}
        if not mime_type.startswith('image/'):
            return {'success':False,'error':'MIME image tidak valid','content':''}
        data_uri=f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        configured=[x.strip() for x in os.getenv('ATA_VISION_MODELS','').split(',') if x.strip()]
        models=[model] if model else (configured or DEFAULT_VISION)
        last=''
        content=[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':data_uri}}]
        for m in models:
            result=self._post_json(CHAT_URL,{'model':m,'messages':[{'role':'user','content':content}],'temperature':0.1,'max_tokens':int(os.getenv('ATA_VISION_MAX_TOKENS','2500'))},timeout=int(os.getenv('ATA_MEDIA_TIMEOUT','75')))
            if not result.get('success'):
                last=result.get('error',''); continue
            data=result['data']; answer=((data.get('choices') or [{}])[0].get('message') or {}).get('content','')
            if isinstance(answer,list): answer='\n'.join(str(x.get('text','')) for x in answer if isinstance(x,dict))
            answer=str(answer).strip()
            if answer:
                return {'success':True,'model':data.get('model',m),'content':answer,'raw':data}
            last='Vision model mengembalikan respons kosong'
        return {'success':False,'error':last or 'Semua vision model gagal','content':''}
