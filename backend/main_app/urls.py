from authapp import views
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),  # For Google OAuth and allauth
    path("accounts/", include("authapp.urls")),  # For custom register/login
    path("", views.index, name="home"),  # Root URL points to new index view
]
