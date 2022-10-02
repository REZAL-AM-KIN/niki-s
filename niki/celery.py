import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niki.settings')

app = Celery('niki')


# - namespace='CELERY' implique que tout les paramètres liés à celery
#   doivent avoir le préfixe `CELERY_`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Chargement des taches automatiquement depuis les apps django enregitrées.
app.autodiscover_tasks()

# Permet de faire du debug de task
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


