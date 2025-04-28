# utils.py

import base64
import os
import re

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from ultralytics import YOLO

# Initialize YOLOv8 model
model = YOLO("yolov8n.pt")


def process_image_with_yolov8(image_path: str, user_id: str) -> str:
    try:
        project_dir = os.path.join(settings.MEDIA_ROOT, "processed_images")
        os.makedirs(project_dir, exist_ok=True)

        results = model.predict(
            source=image_path, save=True, project=project_dir, name=user_id
        )

        save_dir = results[0].save_dir
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        saved_filename = f"{base_name}.jpg"
        saved_path = os.path.join(save_dir, saved_filename)

        # Delete the original file
        if os.path.exists(image_path):
            os.remove(image_path)

        rel_path = os.path.relpath(saved_path, settings.MEDIA_ROOT)
        processed_image_url = f"{settings.MEDIA_URL}{rel_path.replace(os.sep, '/')}"

        return processed_image_url
    except Exception as e:
        raise Exception(f"Error processing image with YOLOv8: {e}")


def send_image_to_lambda(
    image_file,
    filter_type,
    api_url="https://0a489pvuy3.execute-api.us-east-1.amazonaws.com/default/filterfixed",
):
    """
    Send an image to an AWS Lambda function via API Gateway for editing and retrieve the S3 link.

    :param image_file: Either a file object (e.g., from Django request.FILES) or a string (file path)
    :param filter_type: The filter to apply (e.g., 'brightness', 'grayscale', 'invert', 'contrast', 'blur', 'sharpen')
    :param api_url: The API Gateway endpoint URL
    :return: The S3 link to the edited image
    :raises: Exception with detailed message if the request fails
    """
    try:
        valid_filters = {
            "brightness",
            "grayscale",
            "invert",
            "contrast",
            "blur",
            "sharpen",
        }
        if filter_type not in valid_filters:
            raise ValidationError(
                f"Invalid filter type. Must be one of: {', '.join(valid_filters)}"
            )

        if isinstance(image_file, str):
            with open(image_file, "rb") as f:
                image_data = f.read()
        else:
            image_data = image_file.read()
        if os.path.exists(image_file):
            os.remove(image_file)
        base64_encoded = base64.b64encode(image_data).decode("utf-8")
        url = f"{api_url}?filter={filter_type}"
        headers = {"Content-Type": "text/plain"}
        response = requests.post(url, data=base64_encoded, headers=headers)
        response.raise_for_status()

        s3_link = response.text.strip()
        if not s3_link:
            raise ValueError("Empty S3 link returned in API response")
        url_pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
        if not url_pattern.match(s3_link):
            raise ValueError(f"Invalid S3 link format: {s3_link}")
        print(f"{filter_type} - {s3_link}")
        return s3_link

    except requests.exceptions.HTTPError as e:
        error_detail = getattr(e.response, "text", str(e))
        raise Exception(f"API request failed: {str(e)} - Response: {error_detail}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")
    except FileNotFoundError:
        raise Exception(f"Image file not found: {image_file}")
    except ValidationError as e:
        raise e
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")
