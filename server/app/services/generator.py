import httpx

class Generator:
    def __init__(self, settings):
        self.settings = settings

    def generate(self, parameters):
        return self._request(parameters, 'v6')

    def generate_v7_lab(self, parameters):
        if self.settings.mode != 'real' or not self.settings.v7_lab_enabled:
            raise ValueError('Ensayo v7 deshabilitado')
        return self._request(parameters, 'v7-lab')

    def _request(self, parameters, family):
        with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
            response = client.post(self.settings.generator_url,
                headers={'Authorization': 'Bearer ' + self.settings.generator_token},
                json={'parameters': parameters, 'routeros_family':family})
            response.raise_for_status()
            if len(response.content) > 600000:
                raise ValueError('Artefacto excesivo')
            return response.json()
