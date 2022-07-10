from .models import Consommateur


def has_consommateur(user):
    test = False
    consommateur = Consommateur.objects.filter(consommateur=user)
    if consommateur.count() == 1:
        test = True
    return test
