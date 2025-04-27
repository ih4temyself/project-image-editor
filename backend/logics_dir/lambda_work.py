import base64
import re

import requests
from django.core.exceptions import ValidationError


def send_image_to_lambda(
    image_file,
    filter_type,
    api_url="https://0a489pvuy3.execute-api.us-east-1.amazonaws.com/default/filterfixed",
):
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


if __name__ == "__main__":
    # Example for local testing with a file path
    image_path = "/Users/dddd/projects/github/project-image-editor/backend/media/processed_images/75/uploaded_img_b0d8edf446a1-1.jpg"
    filter_type = "grayscale"  # Example filter
    try:
        s3_link = send_image_to_lambda(image_path, filter_type)
        print(f"S3 Link: {s3_link}")
    except Exception as e:
        print(f"Error: {str(e)}")
