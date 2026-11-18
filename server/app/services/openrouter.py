"""Free OpenRouter structured responses, validated by the existing AI schemas."""
import json
import os

import httpx
from pydantic import ValidationError

from server.app.services.ai import AIError

ERROR_MESSAGES = {
    'openrouter_api_key_missing': 'Falta OPENROUTER_API_KEY en server/.env.',
    'openrouter_authentication': 'OpenRouter rechazó la clave. Revisa OPENROUTER_API_KEY.',
    'openrouter_credits': 'OpenRouter rechazó la solicitud por saldo o condiciones de la cuenta.',
    'openrouter_rate_limit': 'OpenRouter alcanzó el límite gratuito. Intenta más tarde.',
    'openrouter_model_unavailable': 'No hay un modelo gratuito compatible disponible. Intenta más tarde o cambia OPENROUTER_MODEL.',
    'openrouter_request_invalid': 'OpenRouter no admite esta solicitud o el modelo no permite JSON estructurado.',
    'openrouter_connection': 'No se pudo conectar con OpenRouter. Revisa la conexión a Internet.',
    'openrouter_timeout': 'OpenRouter tardó demasiado. Intenta nuevamente.',
    'openrouter_invalid_output': 'El modelo no devolvió una respuesta válida. Reintenta o elige otro modelo gratuito.',
    'openrouter_refused': 'El modelo no pudo responder a este diagnóstico.',
    'openrouter_provider_error': 'OpenRouter no pudo completar la consulta. Intenta más tarde.',
}


def parse(settings, schema, prompt, data, client_factory=None):
    key = os.getenv('OPENROUTER_API_KEY', '').strip()
    if not key:
        raise AIError('openrouter_api_key_missing')
    url = settings.openrouter_api_url.rstrip('/')
    if url.endswith('/api/v1'):
        url += '/chat/completions'
    headers = {'Authorization': 'Bearer ' + key}
    if settings.openrouter_http_referer:
        headers['HTTP-Referer'] = settings.openrouter_http_referer
    if settings.openrouter_x_title:
        headers['X-Title'] = settings.openrouter_x_title
    payload = {'model': settings.openrouter_model,
               'messages': [{'role': 'system', 'content': prompt},
                            {'role': 'user', 'content': json.dumps(data, ensure_ascii=False)}],
               'response_format': {'type': 'json_schema', 'json_schema': {
                   'name': schema.__name__, 'strict': True, 'schema': schema.model_json_schema()}},
               'provider': {'require_parameters': True, 'max_price': {'prompt': 0, 'completion': 0}},
               'max_tokens': 4000, 'stream': False}
    try:
        with (client_factory or httpx.Client)(timeout=60, follow_redirects=False) as client:
            response = client.post(url, headers=headers, json=payload)
        codes = {401: 'authentication', 403: 'authentication', 402: 'credits', 429: 'rate_limit',
                 404: 'model_unavailable', 503: 'model_unavailable', 400: 'request_invalid'}
        if response.status_code != 200:
            raise AIError('openrouter_' + codes.get(response.status_code, 'provider_error'))
        if len(response.content) > 1000000:
            raise AIError('openrouter_invalid_output')
        body = response.json()
        if not isinstance(body, dict) or body.get('error'):
            raise AIError('openrouter_provider_error')
        choices = body.get('choices', [])
        if len(choices) != 1 or choices[0].get('finish_reason') != 'stop':
            raise AIError('openrouter_invalid_output')
        message = choices[0]['message']
        if message.get('refusal'):
            raise AIError('openrouter_refused')
        return schema.model_validate_json(message['content'])
    except AIError:
        raise
    except httpx.TimeoutException:
        raise AIError('openrouter_timeout') from None
    except httpx.HTTPError:
        raise AIError('openrouter_connection') from None
    except (ValidationError, ValueError, TypeError, KeyError, IndexError, AttributeError):
        raise AIError('openrouter_invalid_output') from None
