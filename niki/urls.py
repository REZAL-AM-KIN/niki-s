"""niki URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt import views as jwt_views
from appkfet.auth import PianssTokenObtainPairView


schema_view = get_schema_view(title="KIN API")
admin.site.site_header = "Niki admin"

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("status/", include("health_check.urls")),
    path("", include("appuser.urls")),
    path("", include("appmacgest.urls")),
    # path("", include("appkfet.urls")),
    path("", include("appevents.urls")),
    path("api/", include("api.urls"), name="api"),
    path("api/api-auth", include("rest_framework.urls", namespace="rest_framework")),
    path("api-docs", schema_view, name="openapi-schema"),
    path("captcha/", include("captcha.urls")),
    path(
        "api/piansstoken/", PianssTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path(
        "api/token/", jwt_views.TokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path(
        "api/token/refresh/", jwt_views.TokenRefreshView.as_view(), name="token_refresh"
    ),
]

handler404 = "appuser.views.page_not_found_view"
