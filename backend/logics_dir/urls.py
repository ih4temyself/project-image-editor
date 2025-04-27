from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("upload_image/", views.upload_image, name="upload_image"),
    path("delete_image/", views.delete_image, name="delete_image"),
    path("process_with_yolov8/", views.process_with_yolov8, name="process_with_yolov8"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
