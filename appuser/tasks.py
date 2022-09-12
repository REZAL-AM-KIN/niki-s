from celery import shared_task
from django.core.mail import send_mass_mail
from django.template import Context
from django.template.loader import get_template

from .models import Utilisateur
from django.db.models import Q
from datetime import date, timedelta


@shared_task()
def check_user_cotiz_task():
    email_template = get_template("appuser/cotiz_expired_email.txt")
    email_content = email_template.render()

    users = Utilisateur.objects.filter(Q(is_active=True) & Q(date_expiration__lt=date.today()))

    emails = []
    for user in users:
        user.has_cotiz = False
        user.save()

        emails.append(('Niki - Votre cotisation au rezal a expirée', email_content, None, [user.email]))

    send_mass_mail(emails)

@shared_task()
def send_mail_for_cotiz_task():
    email_template = get_template("appuser/cotiz_will_expire_email.txt")

    #On sélectionne les users actifs qui expire dans 6 jours ou moins
    # et qui aucun mail n'a déjà été envoyé les 2 précédents jours

    users = Utilisateur.objects.filter(Q(is_active=True)
                                       & Q(date_expiration__gt=date.today())
                                       & Q(date_expiration__lte=(date.today()+timedelta(days=6)))
                                       & (Q(last_email_date__lte=(date.today()-timedelta(days=2)))
                                          | Q(last_email_date=None))
                                       )

    emails = []
    for user in users:
        context = {
            'expiry_date': user.date_expiration,
            'time_left': (user.date_expiration - date.today()).days
            }

        email_content = email_template.render(context)
        emails.append(('Niki - Expiration de votre cotisation au rezal', email_content, None, [user.email]))
        user.last_email_date = date.today()
        user.save()

    send_mass_mail(emails)

