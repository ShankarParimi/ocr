import os
import subprocess
from distutils import spawn

import logging
logger = logging.getLogger(__name__)

extensions_to_device = {
    "png": "png16m",
    "jpeg": "jpeg",
    "jpg": "jpeg",
    "tiff": "tiff24nc"
}


class PdfToImage:
    def __init__(self, input_file, output_dir, extension):
        """
        @param input_file: location of pdf file
        @output_dir: location of directory where converted images to be saved
        @extension: extension for converted images
        """
        self.input_file = input_file
        self.output_path = output_dir
        self.extension = extension
        # create the output_path  dir if already doesn't exists
        os.makedirs(name=self.output_path, exist_ok=True)

    def to_images(self) -> list:
        """
        Converts all pages of pdf into specified extension
        return: list of absolute paths for all images converted from pdf
        """
        # Check for dependencies. Needs ghost script installed.
        if not spawn.find_executable("gs"):
            raise EnvironmentError("ghostscript not installed.")

        device = extensions_to_device.get(self.extension, None)
        if device is None:
            raise ValueError("extension is not supported")

        gs_cmd = [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-r600x600",
            "-sDEVICE=" + device,
            "-sOutputFile=" + self.output_path + "/" + "%03d." + self.extension,
            self.input_file,
            "-c",
            "quit",
        ]

        logger.info("converting pdf to image")
        _, err = subprocess.Popen(gs_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if err != b'':
            logger.error(err)
            return []

        image_files_path = [self.output_path + "/" + file for file in sorted(os.listdir(self.output_path)) if
                            file.endswith(self.extension)]
        logger.info("completed converting pdf to image")
        return image_files_path
