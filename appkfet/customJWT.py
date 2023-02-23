from rest_framework_simplejwt.authentication import JWTAuthentication

# On surcharge la classe JWTAuthentication pour ajouter un attribut pianss_token a la requete
# Si l'authentification est de type Session, alors auth vaut None
# Sinon si l'auth est de type JWT, alors auth contient (<User>, {<jwt_value>)
# Si l'auth est de type JWT, alors on set request.pianss_token avec le token pian'ss contenue dans le jwt
# Sinon on set request.pianss_token a None
class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Si l'authentification est de type Session, alors auth vaut None
        # Sinon si l'auth est de type JWT, alors auth contient (<User>, {<jwt_value>)
        auth = super().authenticate(request)

        # On initialise pianss_token a None pour que en cas d'authentification via Session ou via JWT classique
        request.pianss_token = None

        # Si on est en authentification via JWT alors on set request.pianss_token avec le token pian'ss contenue dans le jwt
        if auth:
            if len(auth) == 2:
                request.pianss_token = auth[1].get("pianss_token")

        return auth
