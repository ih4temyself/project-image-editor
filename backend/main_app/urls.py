from authapp import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("authapp.urls")),
    path("home/", include("logics_dir.urls")),
    path("", lambda request: redirect("/home/")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
