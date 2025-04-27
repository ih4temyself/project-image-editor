# utils.py

import os

from django.conf import settings
from ultralytics import YOLO

# Initialize YOLOv8 model
model = YOLO("yolov8n.pt")


def process_image_with_yolov8(image_path: str, user_id: str) -> str:
    try:
        # Define the directory for processed images
        project_dir = os.path.join(settings.MEDIA_ROOT, "processed_images")
        os.makedirs(project_dir, exist_ok=True)

        # Process the image with YOLOv8
        results = model.predict(
            source=image_path, save=True, project=project_dir, name=user_id
        )

        # Get the save directory from YOLOv8 results
        save_dir = results[0].save_dir

        # Extract the base name of the input image (without extension)
        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # Construct the saved filename with .jpg extension (YOLOv8 default)
        saved_filename = f"{base_name}.jpg"
        saved_path = os.path.join(save_dir, saved_filename)

        # Generate the correct relative URL
        rel_path = os.path.relpath(saved_path, settings.MEDIA_ROOT)
        processed_image_url = f"{settings.MEDIA_URL}{rel_path.replace(os.sep, '/')}"

        return processed_image_url
    except Exception as e:
        raise Exception(f"Error processing image with YOLOv8: {e}")
