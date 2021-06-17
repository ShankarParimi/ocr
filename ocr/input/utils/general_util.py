def get_file_extension_from_mime_type(mime_type: str) -> str:
    if mime_type.find("/") == -1:
        raise ValueError("{} is not a valid mime_type".format(mime_type))
    return mime_type.split("/")[1]


def get_file_extension_from_file_path(path) -> str:
    extension = ""
    if '.' in path:
        extension = path.rsplit('.', 1)[1].lower()
    return extension
