import io, time
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core import cfg

TEMPLATES_DIR = Path(__file__).parent / 'templates'

jinja = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml', 'txt'])
)

# simple cache for template list (refresh every 10 seconds)
_template_cache = {'mtime': 0.0, 'list': []}
_CACHE_TTL = 10.0

def list_templates() -> List[str]:
    global _template_cache
    now = time.time()
    # check mtime of directory
    try:
        mtime = max(p.stat().st_mtime for p in TEMPLATES_DIR.glob('*.txt')) if any(TEMPLATES_DIR.glob('*.txt')) else 0.0
    except Exception:
        mtime = 0.0
    if now - _template_cache['mtime'] > _CACHE_TTL or mtime != _template_cache.get('dir_mtime'):
        _template_cache['list'] = [p.stem for p in sorted(TEMPLATES_DIR.glob('*.txt'))]
        _template_cache['mtime'] = now
        _template_cache['dir_mtime'] = mtime
    return _template_cache['list']

def render_template(template_key: str, context: Dict[str,Any]) -> Optional[io.BytesIO]:
    try:
        tpl = jinja.get_template(f"{template_key}.txt")
    except Exception:
        return None
    text = tpl.render(**context)
    bio = io.BytesIO(text.encode('utf-8'))
    bio.name = f"{template_key}.txt"
    bio.seek(0)
    return bio

# simple in-memory per-user cooldowns (not persistent, but helps against spam)
_user_cooldowns = {}

def is_rate_limited(user_id: int, action: str, cooldown_seconds: int = 3) -> bool:
    key = f"{user_id}:{action}"
    now = time.time()
    expires = _user_cooldowns.get(key, 0)
    if now < expires:
        return True
    _user_cooldowns[key] = now + cooldown_seconds
    return False

def get_disclaimer() -> str:
    return ("⚠️ Я выдаю шаблоны и общую справочную информацию. Это не заменяет консультацию юриста. " 
            "Если нужно — я помогу связаться с живым специалистом.") 
