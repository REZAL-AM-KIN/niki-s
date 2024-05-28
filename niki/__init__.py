# Permet de s'assurer que celery est bien chargé au démarage de django

from .celery import app as celery_app

__all__ = ('celery_app',)