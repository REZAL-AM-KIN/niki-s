from celery import shared_task

from niki.settings import MACLOOKUP


@shared_task()
def update_maclookup_vendors_list_task():
    print("Updating MACLOOKUP vendors list")
    MACLOOKUP.update_vendors()
