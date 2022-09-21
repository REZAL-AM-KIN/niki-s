from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

from appcom.models import Com_gadz
from appuser.views import is_gadz, has_cotiz, index


@login_required
@user_passes_test(is_gadz, "/")
def com_gadz(request):
    coms = Com_gadz.objects.filter()
    if len(coms)==0:
        return redirect(index)
    return render(request, "appcom/comgadz.html", {"com": coms[0]})

