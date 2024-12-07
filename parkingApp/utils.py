from PIL import Image
import pytesseract
from django.core.files.base import ContentFile
import io

def process_image(image):
    try:
        # Open the uploaded image
        img = Image.open(image)
        print("Image opened successfully.")

        # Perform OCR to extract the license plate text
        ocr_result = pytesseract.image_to_string(img, lang="mn").strip()
        print(f"OCR Result: {ocr_result}")

        # Check if OCR result is empty
        if not ocr_result:
            raise ValueError("OCR failed to extract any text.")

        # Simulate cropping the license plate (adjust dimensions as needed)
        cropped_img = img.crop((0, 0, img.width, img.height // 2))
        print("Image cropped successfully.")

        # Save the cropped image in memory
        cropped_buffer = io.BytesIO()
        cropped_img.save(cropped_buffer, format='JPEG')
        cropped_image_file = ContentFile(cropped_buffer.getvalue(), name="cropped_plate.jpg")
        print("Cropped image file created.")

        return ocr_result, cropped_image_file

    except Exception as e:
        print(f"Error in process_image: {e}")  # Log the error
        raise e
