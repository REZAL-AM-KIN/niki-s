from appkfet.models import Consommateur

from appuser.models import Utilisateur


def get_utilisateur(request):
    try:
        utilisateur = Utilisateur.objects.get(pk=request.user.pk)
    except Utilisateur.DoesNotExist:
        utilisateur = None
    return {"utilisateur": utilisateur}


def get_consommateur(request):
    if request.user.is_authenticated:
        try:
            consommateur = Consommateur.objects.get(consommateur=request.user)
        except Consommateur.DoesNotExist:
            consommateur = None
        return {"consommateur": consommateur}
    return {}
