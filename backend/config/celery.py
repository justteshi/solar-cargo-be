import os
from celery import Celery
from django.conf import settings

# Ensure the Django settings module is set for workers
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.dev'))

app = Celery('solar_cargo')

# Load configuration from Django settings, using CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Stability / resiliency tweaks for Redis transport
app.conf.update({
    # Keep a small pool of connections
    'broker_pool_limit': 10,
    # How long to wait for a connection attempt
    'broker_connection_timeout': 10,
    # Enable retries on startup
    'broker_connection_retry_on_startup': True,
    # Try to reconnect if connection lost
    'broker_connection_retry': True,
    # Heartbeat interval (seconds) to detect dead connections earlier
    'broker_heartbeat': 30,
    # Transport level options (socket keepalive helps in some environments)
    'broker_transport_options': {
        'socket_connect_timeout': 10,
        'socket_keepalive': True,
    },
    # Prevent worker from prefetching too many tasks (reduce memory spikes)
    'worker_prefetch_multiplier': 1,
})


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
