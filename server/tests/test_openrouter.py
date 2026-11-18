import json
from dataclasses import replace

import httpx
import pytest

from server.app.core.config import Settings
from server.app.services.ai import Interpreter, AIError
from server.app.services.catalog_ai import Recommendations
from server.app.services.openrouter import parse


def settings(**kwargs):
    return Settings('unused.sqlite3', 't'*40, 'a'*40, 'g'*40, 'http://localhost/api', ai_mode='openrouter', **kwargs)


def factory(handler):
    return lambda **kwargs: httpx.Client(transport=httpx.MockTransport(handler), **kwargs)


def test_request_uses_only_openrouter_key_and_validates_schema(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'fake-router')
    monkeypatch.setenv('OPENAI_API_KEY', 'unused-openai')
    def handle(request):
        assert str(request.url) == 'https://openrouter.ai/api/v1/chat/completions'
        assert request.headers['Authorization'] == 'Bearer fake-router'
        assert request.headers['HTTP-Referer'] == 'http://localhost'
        assert request.headers['X-Title'] == 'Soporte remoto inteligente'
        body = json.loads(request.content)
        assert body['model'] == 'openrouter/free'
        assert body['provider']['max_price'] == {'prompt': 0, 'completion': 0}
        assert body['provider']['require_parameters'] is True
        assert body['response_format']['json_schema']['strict'] is True
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {
            'content': json.dumps({'summary': 'Dos enlaces WAN.', 'suggestions': [{'procedure': 'ECMP', 'reason': 'Revisar balanceo.'}]})}}]})
    result = parse(settings(openrouter_api_url='https://openrouter.ai/api/v1'), Recommendations, 'Analiza', {}, factory(handle))
    assert result.suggestions[0].procedure == 'ECMP'


@pytest.mark.parametrize('status,code', [(401,'authentication'),(402,'credits'),(429,'rate_limit'),(404,'model_unavailable'),(503,'model_unavailable'),(400,'request_invalid'),(500,'provider_error')])
def test_provider_errors_are_sanitized(monkeypatch,status,code):
    monkeypatch.setenv('OPENROUTER_API_KEY','fake')
    with pytest.raises(AIError) as exc:
        parse(settings(), Recommendations, '', {}, factory(lambda _:httpx.Response(status,json={'error':'SECRET'})))
    assert exc.value.code == 'openrouter_' + code
    assert 'SECRET' not in str(exc.value)


@pytest.mark.parametrize('content', ['not json', '{"summary":"ok","suggestions":[{"procedure":"DELETE","reason":"bad"}]}', '{"summary":"ok","suggestions":[],"commands":"bad"}'])
def test_invalid_model_response_is_rejected(monkeypatch,content):
    monkeypatch.setenv('OPENROUTER_API_KEY','fake')
    with pytest.raises(AIError,match='openrouter_invalid_output'):
        parse(settings(),Recommendations,'',{},factory(lambda _:httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':content}}]})))


def test_missing_key_never_uses_openai(monkeypatch):
    monkeypatch.delenv('OPENROUTER_API_KEY',raising=False)
    monkeypatch.setenv('OPENAI_API_KEY','unused')
    with pytest.raises(AIError,match='openrouter_api_key_missing'):
        Interpreter(settings())._parse(Recommendations,'',{})


@pytest.mark.parametrize('values',[{'openrouter_model':'openai/gpt-4o'}, {'openrouter_api_url':'https://example.com/api/v1'}, {'openrouter_x_title':'bad\nheader'}])
def test_invalid_configuration(values):
    with pytest.raises(ValueError):
        settings(**values)


def test_all_interpreter_operations_route_to_openrouter(monkeypatch):
    from server.app.services import openrouter
    from server.app.ai.models import ProblemClassification
    calls=[]
    def mock(settings,schema,prompt,data):
        calls.append(schema.__name__)
        return schema.model_validate({'procedure':'ECMP'})
    monkeypatch.setattr(openrouter,'parse',mock)
    assert Interpreter(settings()).classify_problem('ECMP').procedure=='ECMP'
    assert calls==['ProblemClassification']
