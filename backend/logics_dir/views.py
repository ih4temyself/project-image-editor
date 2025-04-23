import os
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.text import slugify


def index(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "index.html", {"form": form})


@login_required
def upload_image(request):
    if request.method == "POST" and request.FILES.get("image"):
        # Get the uploaded file
        image_file = request.FILES["image"]

        # Split the filename into the name and extension
        base_name, extension = os.path.splitext(image_file.name)

        # Sanitize the base name (remove non-alphanumeric characters, replace spaces, etc.)
        sanitized_base_name = slugify(base_name)
        sanitized_base_name = re.sub(
            r"[^a-zA-Z0-9.-]", "_", sanitized_base_name
        )  # Replace spaces/special chars with underscores

        # Combine the sanitized base name with the original extension
        sanitized_filename = f"{sanitized_base_name}{extension}"

        # Save the image to the media folder
        file_name = f"uploaded_{sanitized_filename}"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        # Save the image file
        with open(file_path, "wb") as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # Get the URL to access the image
        file_url = os.path.join("/home/media", file_name)
        print(file_url)

        # Return the file URL to frontend (instead of passing `uploaded_image` directly)
        return JsonResponse(
            {"message": "Image uploaded successfully", "file_url": file_url}
        )

    return JsonResponse({"error": "Invalid request or no image uploaded."}, status=400)
