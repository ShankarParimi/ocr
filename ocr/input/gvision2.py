import os
import shutil
import time
from .utils import general_util as util
from .utils import image_enhancer as img_enh
from .utils import pdftoimage as p2i

import logging

logger = logging.getLogger(__name__)

__supported_img_extensions = ["png", "jpg", "jpeg", "tiff"]
__extension = "png"
__threshold_number = 25


def to_text(path):
    """
    if the file extension is from list __supported_img_extensions directly run the gvision on input file,
    if the input file is pdf convert it into images using PdfToImage and Convert each image to gray scale
    using ImageEnhancer, run the gvision for each converted image and concatenate the extracted texts for each image,
    delete the converted images
    """
    file_extension = util.get_file_extension_from_file_path(path)
    if file_extension == "":
        return "".encode("utf-8")

    if file_extension in __supported_img_extensions:
        try:
            img_enhancer = img_enh.ImageEnhancer(path)
            if not img_enhancer.to_gray_scale():
                return "".encode("utf-8")
            text = get_document_text_by_gvision(path)
        except Exception as e:
            print(f"Exception: {e}")
            return "".encode("utf-8")
        return text.encode("utf-8")
    elif file_extension == "pdf":
        logger.info("pdf extension found it will take some time to extract text")
        output_dir = "/tmp/temp"
        try:
            logger.debug(f"creating  dir {output_dir}")
            os.makedirs(name=output_dir, exist_ok=True)
        except Exception as e:
            logger.error(e)
            return "".encode("utf-8")
        pdf_to_image = p2i.PdfToImage(path, output_dir, __extension)
        image_files_path = pdf_to_image.to_images()
        print(image_files_path)
        # time.sleep(30)
        if len(image_files_path) > __threshold_number:
            image_files_path = []
        print(image_files_path)
        # return "".encode("utf-8")

        extracted_str = ""
        for image_path in image_files_path:
            image_enhancer = img_enh.ImageEnhancer(image_path)
            if not image_enhancer.to_gray_scale():
                extracted_str = ""
                break
            try:
                logger.info("applying gvision on the image")
                text = get_document_text_by_gvision(image_path)
                logger.info("completed gvision on the image")
                logger.info(f"text: {text.encode('utf-8')}")
            except (FileNotFoundError, Exception) as e:
                logger.error(f"failed to extract from image using gvision - {e}")
                extracted_str = ""
                break
            extracted_str += text + "\n"

        logger.debug(f"deleting  dir {output_dir}")
        __delete_dir(output_dir)
        return extracted_str.encode("utf-8")

    else:
        raise ValueError("file extension {} is not supported".format(file_extension))


def __delete_dir(temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# -*- coding: utf-8 -*-
def get_text_by_gvision(path, lang='fr'):
    """Detects text in the file."""
    from google.cloud import vision
    import io

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    texts = response.full_text_annotation.text
    return texts


def get_document_text_by_gvision(path, lang='fr'):
    """Detects text in the file."""
    from google.cloud import vision
    import io

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    texts = response.full_text_annotation.text
    return texts
