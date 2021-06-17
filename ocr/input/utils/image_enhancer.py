import subprocess
from distutils import spawn

import logging
logger = logging.getLogger(__name__)


class ImageEnhancer:
    def __init__(self, image_path):
        self.image_path = image_path

    def to_gray_scale(self):
        """
        Converts the image into gray scale and save image as was saved earlier
        return: True when successful conversion else return False
        """
        if not spawn.find_executable("convert"):
            raise EnvironmentError("imagemagick not installed.")

        # Enhance Image
        magick_cmd = [
            "convert",
            self.image_path,
            "-colorspace",
            "gray",
            "-type",
            "grayscale",
            "-contrast-stretch",
            "0",
            "-sharpen",
            "0x1",
            self.image_path,
        ]
        logger.info("converting image into gray scale")
        out, err = subprocess.Popen(magick_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if err != b'':
            logger.error(err)
            return False
        logger.info("completed converting image into gray scale")
        return True
