import os

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

from .utils import process_image_with_yolov8


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

        # Process and save the image as you are doing now
        base_name, extension = os.path.splitext(image_file.name)
        sanitized_base_name = slugify(base_name)
        sanitized_filename = f"{sanitized_base_name}{extension}"
        file_name = f"uploaded_{sanitized_filename}"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        # Save the file
        with open(file_path, "wb") as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # Save the relative image URL to session (no need for '/home' part)
        image_url = f"/home/media/{file_name}"  # Use '/media' prefix here for proper reference
        request.session["uploaded_image_url"] = image_url  # Save to session
        print(image_url)
        # Return the file URL to frontend
        return JsonResponse(
            {"message": "Image uploaded successfully", "file_url": image_url}
        )

    return JsonResponse({"error": "Invalid request or no image uploaded."}, status=400)


@login_required
def delete_image(request):
    """
    View to delete the uploaded image from the server.
    """
    image_url = request.session.get("uploaded_image_url")

    if not image_url:
        return JsonResponse({"error": "No image uploaded"}, status=400)

    # Remove the "/media/" prefix from the image_url to get the file name
    file_name = os.path.basename(image_url)
    print(file_name)
    # Construct the full image path by combining MEDIA_ROOT with the file_name
    image_path = os.path.join(settings.MEDIA_ROOT, file_name)
    print(image_path)

    try:
        # Check if the image exists, and delete it if it does
        if os.path.exists(image_path):
            os.remove(image_path)
        else:
            return JsonResponse({"error": f"Image not found at {image_path}"}, status=404)

        # Clear the image URL from the session
        del request.session["uploaded_image_url"]

        return JsonResponse({"message": "Image deleted successfully"})
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@login_required
def process_with_yolov8(request):
    """
    View that processes the image using YOLOv8 and returns the processed image URL.
    """
    # Get the uploaded image URL from the session
    image_url = request.session.get("uploaded_image_url")

    if not image_url:
        return JsonResponse({"error": "No image uploaded"}, status=400)

    # Construct the full image path from the URL
    # Strip "/media/" and get the relative file path
    file_name = image_url.lstrip("/media/")
    image_path = os.path.join(settings.MEDIA_ROOT, file_name)

    try:
        # Process the image with YOLOv8 using the utility function
        processed_image_url = process_image_with_yolov8(
            image_path, str(request.user.id)
        )

        # Return the processed image URL in the response
        return JsonResponse(
            {"message": "Image processed successfully", "file_url": processed_image_url}
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)