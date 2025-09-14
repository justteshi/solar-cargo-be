from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'solarcargo.commitandpray.com']
INSTALLED_APPS += ['storages']

# Celery configuration (use redis service from docker-compose by default)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL') or 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND') or 'redis://redis:6379/1'

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STORAGES = {
    # Media file (image) management
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
    },

    # CSS and JS file management
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",  # Local static files
    },
}

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'https://solarcargo.commitandpray.com',
]