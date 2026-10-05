import httpx

class Generator:
    def __init__(self, settings):
        self.settings = settings

    def generate(self, parameters):
        with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
            response = client.post(self.settings.generator_url,
                headers={'Authorization': 'Bearer ' + self.settings.generator_token},
                json={'parameters': parameters, 'routeros_family':'v6'})
            response.raise_for_status()
            if len(response.content) > 600000:
                raise ValueError('Artefacto excesivo')
            return response.json()
