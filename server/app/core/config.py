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

    def __post_init__(self):
        tokens = [self.technician_token, self.agent_token, self.generator_token]
        if any(len(t) < 32 for t in tokens) or len(set(tokens)) != 3:
            raise ValueError('Se requieren tres tokens distintos de al menos 32 caracteres')
        if self.mode not in ('real','simulated') or self.ai_mode not in ('openai','simulated'):
            raise ValueError('Modo invalido')
        secure_url(self.generator_url)

    @classmethod
    def from_env(cls):
        load_dotenv('server/.env')
        return cls(database=os.getenv('ECMP_DATABASE','server/mvp.sqlite3'),
                   technician_token=os.environ['ECMP_TECHNICIAN_TOKEN'], agent_token=os.environ['ECMP_AGENT_TOKEN'],
                   generator_token=os.environ['ECMP_GENERATOR_TOKEN'], generator_url=os.environ['ECMP_GENERATOR_URL'],
                   mode=os.getenv('ECMP_MODE','real'), ai_mode=os.getenv('ECMP_AI_MODE','simulated'),
                   technician_id=os.getenv('ECMP_TECHNICIAN_ID','technician-1'), agent_id=os.getenv('ECMP_AGENT_ID','agent-1'),
                   openai_model=os.getenv('OPENAI_MODEL','gpt-4o-mini'))
