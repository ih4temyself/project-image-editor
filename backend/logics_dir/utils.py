# utils.py
from ultralytics import YOLO
import os
from PIL import Image
from django.conf import settings

# Initialize YOLOv8 model (You can modify this to use any YOLOv8 model variant, such as yolov8n.pt)
model = YOLO("yolov8n.pt")


def process_image_with_yolov8(image_path: str, user_id: str):
    try:
        # Open the image
        img = Image.open(image_path)

        # Run YOLOv8 inference on the image
        results = model(img)

        # Save annotated image with a user-specific name to avoid conflicts
        user_directory = os.path.join(settings.MEDIA_ROOT, "processed_images", user_id)
        os.makedirs(user_directory, exist_ok=True)

        # Save annotated image
        results.save(path=user_directory)

        # Get the path of the saved annotated image
        annotated_image_path = results.files[
            0
        ]  # The first file in the results (which is the annotated image)
        annotated_image_url = os.path.join(
            "/media/processed_images", user_id, os.path.basename(annotated_image_path)
        )

        return annotated_image_url

    except Exception as e:
        raise Exception(f"Error processing image with YOLOv8: {str(e)}")
