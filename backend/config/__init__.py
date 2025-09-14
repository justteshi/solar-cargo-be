# Intentionally do not import the Celery app here to avoid side-effects during Django startup
# Celery worker will load config.celery directly via the -A argument.
__all__ = []

