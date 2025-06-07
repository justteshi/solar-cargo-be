from .base import *

DEBUG = True

ALLOWED_HOSTS = ['solarcargo.commitandpray.com']

CSRF_TRUSTED_ORIGINS = [
    'https://solarcargo.commitandpray.com',
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')