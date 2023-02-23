from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework import serializers

from appkfet.models import Pianss

"""
Authentication pour les pian'ss
"""
class PianssTokenObtainPairSerializer(TokenObtainPairSerializer):
    pianss_token = serializers.CharField()

    def validate(self, attrs):
        self.pianss_token = attrs.pop('pianss_token')
        if not self.pianss_token:
            raise serializers.ValidationError("A pian'ss token is required.")

        pianss = Pianss.objects.filter(token=self.pianss_token)

        if len(pianss) == 0:
            raise serializers.ValidationError("Invalid pian'ss token.")

        validated_data = super().validate(attrs)
        #validated_data['pianss_token'] = self.pianss_token
        return validated_data

    def get_token(self, user):
        token = super().get_token(user)

        # Add custom claims
        token['pianss_token'] = self.pianss_token

        return token


class PianssTokenObtainPairView(TokenObtainPairView):
    serializer_class = PianssTokenObtainPairSerializer



