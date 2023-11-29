from rest_framework_simplejwt.authentication import JWTAuthentication

# On surcharge la classe JWTAuthentication pour ajouter un attribut pianss_token a la requete
# Si l'authentification est de type Session, alors auth vaut None
# Sinon si l'auth est de type JWT, alors auth contient (<User>, {<jwt_value>)
# Si l'auth est de type JWT, alors on set request.pianss_token avec le token pian'ss contenue dans le jwt
# Sinon on set request.pianss_token a None
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from appkfet.models import Pianss


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):

        # Si l'authentification est de type Session, alors auth vaut None
        # Sinon si l'auth est de type JWT, alors auth contient (<User>, {<jwt_value>)
        auth = super().authenticate(request)

        # Si on est en authentification via JWT alors on set request.pianss_token avec le token pian'ss contenue dans le jwt
        if auth:
            if len(auth) == 2:
                pian_token = auth[1].get("pianss_token")
                if pian_token is not None:
                    request.pianss_token = pian_token

        return auth

    # On surcharge la methode get_validated_token pour verifier que le token pian'ss est valide (verfier si le pian'ss existe)
    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)
        pianss_token = validated_token.get("pianss_token")

        # Si un token pian'ss est present dans le jwt, alors on verifie qu'il est valide
        if pianss_token is not None:
            if not Pianss.objects.filter(token=pianss_token).exists():
                raise InvalidToken("Invalid pian'ss token.")

        return validated_token
