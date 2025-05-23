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

from .utils import process_image_with_yolov8, send_image_to_lambda


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
        image_file = request.FILES["image"]
        base_name, extension = os.path.splitext(image_file.name)
        sanitized_base_name = slugify(base_name)
        sanitized_filename = f"{sanitized_base_name}{extension}"
        file_name = f"uploaded_{sanitized_filename}"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        with open(file_path, "wb") as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        image_url = f"{settings.MEDIA_URL}{file_name}"
        request.session["uploaded_image_url"] = image_url
        return JsonResponse(
            {"message": "Image uploaded successfully", "file_url": image_url}
        )

    return JsonResponse({"error": "Invalid request or no image uploaded."}, status=400)

@login_required
def delete_image(request):
    uploaded_image_url = request.session.get("uploaded_image_url")
    original_image_url = request.session.get("original_image_url")
    
    if not uploaded_image_url:
        return JsonResponse({"error": "No image uploaded"}, status=400)

    try:
        # Delete the uploaded/processed image
        uploaded_file_path = uploaded_image_url.replace(settings.MEDIA_URL, settings.MEDIA_ROOT).replace('/', os.sep)
        uploaded_file_path = os.path.normpath(uploaded_file_path)  # Normalize path

        if os.path.exists(uploaded_file_path):
            os.remove(uploaded_file_path)

        # Delete the original image if it exists and is different
        if original_image_url and original_image_url != uploaded_image_url:
            original_file_path = original_image_url.replace(settings.MEDIA_URL, settings.MEDIA_ROOT).replace('/', os.sep)
            original_file_path = os.path.normpath(original_file_path)
            if os.path.exists(original_file_path):
                os.remove(original_file_path)

        # Clean up processed image directory for YOLOv8
        base_name = os.path.splitext(os.path.basename(uploaded_file_path))[0]
        processed_dir = os.path.join(settings.MEDIA_ROOT, "processed_images", str(request.user.id))
        processed_file = os.path.join(processed_dir, f"{base_name}.jpg")

        if os.path.exists(processed_file):
            os.remove(processed_file)

        # Remove processed directory if empty
        if os.path.exists(processed_dir) and not os.listdir(processed_dir):
            os.rmdir(processed_dir)

        # Clear session data
        if "uploaded_image_url" in request.session:
            del request.session["uploaded_image_url"]
        if "original_image_url" in request.session:
            del request.session["original_image_url"]

        return JsonResponse({"message": "Image deleted successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def process_with_yolov8(request):
    image_url = request.session.get("uploaded_image_url")
    if not image_url:
        return JsonResponse({"error": "No image uploaded"}, status=400)

    file_name = os.path.basename(image_url)
    image_path = os.path.join(settings.MEDIA_ROOT, file_name)

    try:
        processed_image_url = process_image_with_yolov8(
            image_path, str(request.user.id)
        )
        request.session["uploaded_image_url"] = processed_image_url
        return JsonResponse(
            {"message": "Image processed successfully", "file_url": processed_image_url}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def apply_filter(request):
    """
    View to apply a Lambda-based filter to the uploaded image.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    image_url = request.session.get("uploaded_image_url")
    if not image_url:
        return JsonResponse({"error": "No image uploaded"}, status=400)

    filter_type = request.POST.get("filter")
    if not filter_type:
        return JsonResponse({"error": "No filter specified"}, status=400)

    file_name = os.path.basename(image_url)
    image_path = os.path.join(settings.MEDIA_ROOT, file_name)

    try:
        # Apply the filter using the Lambda function
        s3_link = send_image_to_lambda(image_path, filter_type)
        # Update session with the new S3 link
        request.session["uploaded_image_url"] = s3_link
        return JsonResponse(
            {"message": "Filter applied successfully", "file_url": s3_link}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
