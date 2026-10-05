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
    'fast': ['qwen/qwen3.8-27b:free','google/gemma-4-31b-it:free'],
    'prose': ['google/gemma-4-31b-it:free','qwen/qwen3.8-27b:free'],
    'reasoning': ['nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free','google/gemma-4-31b-it:free'],
}
DEFAULT_VISION = ['google/gemini-2.5-flash', 'openai/gpt-4o-mini']


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


def _configured_key() -> str:
    if 'OPENROUTER_API_KEY' in os.environ:
        return os.environ['OPENROUTER_API_KEY'].strip()
    data_dir = os.getenv('ATA_DATA_DIR', '')
    if os.getenv('ATA_TESTING') or ('temp' in data_dir.lower() or 'tmp' in data_dir.lower()):
        return ''
    try:
        from pathlib import Path
        cfg = Path(__file__).resolve().parent.parent / '.env.local'
        if cfg.is_file():
            for line in cfg.read_text(encoding='utf-8').splitlines():
                if line.startswith('OPENROUTER_API_KEY='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return ''

class OpenRouterClient:
    def __init__(self, api_key: Optional[str]=None):
        self.api_key = api_key
    def get_key(self) -> str:
        if self.api_key is not None:
            return self.api_key
        return _configured_key()
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
        for m in ([model] if model else _env_models(tier)):
            result=self._post_json(CHAT_URL,{'model':m,'messages':messages,'temperature':temperature,'max_tokens':limit},timeout=60)
            if not result.get('success'):
                last=result.get('error',''); continue
            data=result['data']; content=((data.get('choices') or [{}])[0].get('message') or {}).get('content','')
            if isinstance(content,list):
                content='\n'.join(str(x.get('text','')) for x in content if isinstance(x,dict) and x.get('type')=='text')
            if len(str(content).strip())<8 or str(content).strip().startswith('User Safety:'):
                last='empty or safety stub response'; continue
            return {'success':True,'model':data.get('model',m),'content':str(content),'raw':data}
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
        result=self._post_json(TRANSCRIPTION_URL,payload,timeout=int(os.getenv('ATA_MEDIA_TIMEOUT','60')))
        if not result.get('success'): return {'success':False,'error':result.get('error','Transkripsi gagal'),'text':''}
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
            result=self._post_json(CHAT_URL,{'model':m,'messages':[{'role':'user','content':content}],'temperature':0.1,'max_tokens':int(os.getenv('ATA_VISION_MAX_TOKENS','2500'))},timeout=int(os.getenv('ATA_MEDIA_TIMEOUT','60')))
            if not result.get('success'):
                last=result.get('error',''); continue
            data=result['data']; answer=((data.get('choices') or [{}])[0].get('message') or {}).get('content','')
            if isinstance(answer,list): answer='\n'.join(str(x.get('text','')) for x in answer if isinstance(x,dict))
            answer=str(answer).strip()
            if answer:
                return {'success':True,'model':data.get('model',m),'content':answer,'raw':data}
            last='Vision model mengembalikan respons kosong'
        return {'success':False,'error':last or 'Semua vision model gagal','content':''}
