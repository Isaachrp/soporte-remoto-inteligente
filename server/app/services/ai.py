"""One provider boundary. Simulated mode is explicit; never an error fallback."""
import json
import os
import re
from typing import Protocol

from pydantic import ValidationError
from server.app.ai.models import ProblemClassification, SupportPlan, ResultAnalysis
from server.app.ai import prompts
from shared.contracts import ACTIONS

Classification = ProblemClassification  # Compatibility alias, not a second schema.


class AIError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def request_projection(text):
    """Preserve the existing privacy boundary: no raw prose or credentials leave."""
    words = re.findall(r'\b(?:ecmpr|ecmp|pcc|hotspot|windows|impresora|recursivo)\b', text.lower())
    return 'ECMP' if words and set(words) == {'ecmp'} else 'OUT_OF_SCOPE'


class AIService(Protocol):
    def classify_problem(self, intent: str) -> ProblemClassification: ...
    def generate_plan(self, classification: ProblemClassification, parameters_present: bool) -> SupportPlan: ...
    def analyze_results(self, evidence: dict) -> ResultAnalysis: ...


def expected_analysis(status):
    values = {
        'configuration_with_warnings': ('configuration_checked', True, 'test_wan_lan'),
        'configuration_failed': ('verification_failed', True, 'review_manually'),
        'intervention_required': ('needs_human_review', True, 'review_manually'),
    }
    assessment, intervention, next_step = values.get(status, ('not_executed', False, 'submit_new_request'))
    return ResultAnalysis(assessment=assessment, problem_resolved=False,
                          requires_human_intervention=intervention, next_step=next_step)


class Interpreter:
    def __init__(self, settings, client_factory=None):
        self.settings = settings
        self.client_factory = client_factory

    def _parse(self, schema, system_prompt, data):
        if self.settings.ai_mode == 'openrouter':
            from server.app.services.openrouter import parse
            return parse(self.settings, schema, system_prompt, data)
        if not os.getenv('OPENAI_API_KEY', '').strip():
            raise AIError('openai_api_key_missing')
        from openai import OpenAI, APITimeoutError, LengthFinishReasonError, ContentFilterFinishReasonError
        try:
            factory = self.client_factory or OpenAI
            with factory(timeout=20, max_retries=0) as client:
                # SDK 1.82.0 exposes Pydantic parsing under beta.chat.
                response = client.beta.chat.completions.parse(
                    model=self.settings.openai_model,
                    messages=[{'role': 'system', 'content': system_prompt},
                              {'role': 'user', 'content': json.dumps(data, sort_keys=True)}],
                    response_format=schema, max_completion_tokens=1800, store=False)
            if len(response.choices) != 1 or response.choices[0].finish_reason != 'stop':
                raise AIError('ai_incomplete_output')
            message = response.choices[0].message
            if message.refusal or message.parsed is None:
                raise AIError('ai_refused')
            return schema.model_validate(message.parsed)
        except AIError:
            raise
        except APITimeoutError:
            raise AIError('ai_timeout') from None
        except LengthFinishReasonError:
            raise AIError('ai_incomplete_output') from None
        except ContentFilterFinishReasonError:
            raise AIError('ai_refused') from None
        except ValidationError:
            raise AIError('ai_invalid_output') from None
        except Exception:
            raise AIError('ai_provider_error') from None

    def classify_problem(self, intent):
        if intent not in ('ECMP', 'OUT_OF_SCOPE'):
            raise AIError('invalid_intent_projection')
        if self.settings.ai_mode == 'simulated' or intent == 'OUT_OF_SCOPE':
            return ProblemClassification(procedure=intent)
        return self._parse(ProblemClassification, prompts.CLASSIFY, {'requested_procedure': intent})

    def classify(self, text):
        """Compatibility API used by existing callers/tests."""
        return self.classify_problem(request_projection(text)).procedure

    def generate_plan(self, classification, parameters_present):
        if self.settings.ai_mode != 'simulated' and classification.procedure != 'OUT_OF_SCOPE':
            return self._parse(SupportPlan, prompts.planning_prompt(), {
                'classification': classification.model_dump(), 'parameters_present': parameters_present})
        supported = classification.procedure == 'ECMP'
        ready = supported and parameters_present
        reasons = {'get_ecmp_precheck': 'Comprobar condiciones del router.',
                   'apply_approved_ecmp': 'Aplicar el artefacto solo tras aprobacion humana.',
                   'verify_ecmp': 'Contrastar la configuracion resultante.'}
        return SupportPlan(category=classification.procedure,
            explanation='Procedimiento ECMP supervisado.' if supported else 'Solicitud fuera del MVP ECMP.',
            status='ready' if ready else 'needs_information' if supported else 'out_of_scope',
            missing_information=['ecmp_parameters'] if supported and not parameters_present else [],
            actions=[{'action_id': name, 'parameters': {}, 'reason': reasons[name],
                      'risk_level': 'REQUIRES_APPROVAL' if rule['risk'] == 'write' else 'READ_ONLY',
                      'requires_approval': rule['risk'] == 'write'}
                     for name, rule in ACTIONS.items()] if ready else [])

    def analyze_results(self, evidence):
        if self.settings.ai_mode == 'simulated':
            return expected_analysis(evidence['status'])
        return self._parse(ResultAnalysis, prompts.ANALYZE, evidence)
