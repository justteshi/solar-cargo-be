from drf_spectacular.extensions import OpenApiAuthenticationExtension

class APIKeyFallbackAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'authentication.authentication.APIKeyAuthentication'
    name = 'ApiKeyAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Use format: Api-Key <your-key>',
        }
