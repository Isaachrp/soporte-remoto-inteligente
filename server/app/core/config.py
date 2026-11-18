import os
from dataclasses import dataclass
from urllib.parse import urlparse
from dotenv import load_dotenv

def secure_url(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1','localhost','testserver')):
        raise ValueError('HTTPS requerido fuera de loopback')
    if parsed.username or parsed.password:
        raise ValueError('Credenciales en URL prohibidas')
    return url

@dataclass
class Settings:
    database: str
    technician_token: str
    agent_token: str
    generator_token: str
    generator_url: str
    technician_id: str = 'technician-1'
    agent_id: str = 'agent-1'
    mode: str = 'real'
    ai_mode: str = 'simulated'
    openai_model: str = 'gpt-4o-mini'
    session_seconds: int = 3600
    heartbeat_seconds: int = 45
    approval_seconds: int = 300
    v7_lab_enabled: bool = False
    openrouter_api_url: str = 'https://openrouter.ai/api/v1/chat/completions'
    openrouter_model: str = 'openrouter/free'
    openrouter_http_referer: str = 'http://localhost'
    openrouter_x_title: str = 'Soporte remoto inteligente'

    def __post_init__(self):
        tokens = [self.technician_token, self.agent_token, self.generator_token]
        if any(len(t) < 32 for t in tokens) or len(set(tokens)) != 3:
            raise ValueError('Se requieren tres tokens distintos de al menos 32 caracteres')
        if self.mode not in ('real','simulated') or self.ai_mode not in ('openai','openrouter','simulated'):
            raise ValueError('Modo invalido')
        if type(self.v7_lab_enabled) is not bool or (self.v7_lab_enabled and self.mode != 'real'):
            raise ValueError('Ensayo v7 requiere modo real y habilitacion explicita')
        secure_url(self.generator_url)
        if self.ai_mode == 'openrouter':
            url = urlparse(self.openrouter_api_url)
            if (url.scheme != 'https' or url.hostname != 'openrouter.ai' or url.username or url.password
                    or url.query or url.fragment or url.port not in (None, 443)
                    or url.path.rstrip('/') not in ('/api/v1', '/api/v1/chat/completions')):
                raise ValueError('OPENROUTER_API_URL debe apuntar a https://openrouter.ai/api/v1/chat/completions')
            if self.openrouter_model != 'openrouter/free' and not self.openrouter_model.endswith(':free'):
                raise ValueError('Selecciona openrouter/free o un modelo terminado en :free.')
            for value in (self.openrouter_http_referer, self.openrouter_x_title):
                if '\r' in value or '\n' in value or not value.isascii():
                    raise ValueError('Los encabezados OpenRouter requieren texto ASCII sin saltos de línea.')

    @classmethod
    def from_env(cls):
        load_dotenv('server/.env')
        return cls(database=os.getenv('ECMP_DATABASE','server/mvp.sqlite3'),
                   technician_token=os.environ['ECMP_TECHNICIAN_TOKEN'], agent_token=os.environ['ECMP_AGENT_TOKEN'],
                   generator_token=os.environ['ECMP_GENERATOR_TOKEN'], generator_url=os.environ['ECMP_GENERATOR_URL'],
                   mode=os.getenv('ECMP_MODE','real'), ai_mode=os.getenv('ECMP_AI_MODE','simulated'),
                   technician_id=os.getenv('ECMP_TECHNICIAN_ID','technician-1'), agent_id=os.getenv('ECMP_AGENT_ID','agent-1'),
                   openai_model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),
                   openrouter_api_url=os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions').strip(),
                   openrouter_model=os.getenv('OPENROUTER_MODEL', 'openrouter/free').strip(),
                   openrouter_http_referer=os.getenv('OPENROUTER_HTTP_REFERER', 'http://localhost').strip(),
                   openrouter_x_title=os.getenv('OPENROUTER_X_TITLE', 'Soporte remoto inteligente').strip(),
                   v7_lab_enabled=os.getenv('ECMP_V7_LAB_ENABLED', '0') == '1')
