from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        auth = super().authenticate(request)
        request.machine_id = "salss"

        return auth
