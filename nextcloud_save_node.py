import base64
import io
import os
from datetime import datetime
from urllib import error, parse, request
import numpy as np
from PIL import Image


def _build_auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _split_remote_path(remote_path: str) -> list[str]:
    return [segment for segment in remote_path.strip("/").split("/") if segment]


def _webdav_root(base_url: str, username: str) -> str:
    quoted_user = parse.quote(username, safe="")
    return f"{_normalize_base_url(base_url)}/remote.php/dav/files/{quoted_user}"


def _mkdir_if_missing(url: str, auth_header: str) -> None:
    req = request.Request(url, method="MKCOL")
    req.add_header("Authorization", auth_header)
    try:
        request.urlopen(req)
    except error.HTTPError as exc:
        if exc.code not in (301, 405):
            raise


def _ensure_remote_directory(base_url: str, username: str, password: str, remote_path: str) -> str:
    auth_header = _build_auth_header(username, password)
    current_url = _webdav_root(base_url, username)

    for segment in _split_remote_path(remote_path):
        current_url = f"{current_url}/{parse.quote(segment, safe='')}"
        _mkdir_if_missing(current_url, auth_header)

    return current_url

def _tensor_to_image(image_tensor):
    image = 255.0 * image_tensor.cpu().numpy()
    image = np.clip(image, 0, 255).astype(np.uint8)
    pil_image = Image.fromarray(image)
    return pil_image

def _image_to_png_bytes(pil_image) -> bytes:
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _save_preview_file(filename, pil_image) -> dict[str, str] | None:
    try:
        import folder_paths
    except ImportError:
        return None

    temp_dir = folder_paths.get_temp_directory()
    filepath = os.path.join(temp_dir, filename);

    pil_image.save(filepath)

    return {
        "filename": filename,
        "subfolder": temp_dir,
        "type": "temp",
    }


def _upload_file(upload_url: str, auth_header: str, payload: bytes) -> None:
    req = request.Request(upload_url, data=payload, method="PUT")
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "image/png")
    req.add_header("Content-Length", str(len(payload)))
    request.urlopen(req)


class SaveImageToNextcloud:
    CATEGORY = "image/output"
    FUNCTION = "save_images"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    def __init__(self):
        self.type = "temp"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "base_url": ("STRING", {"default": "https://nextcloud.example.com"}),
                "username": ("STRING", {"default": "username"}),
                "password": ("STRING", {"default": ""}),
                "remote_path": ("STRING", {"default": "Photos/ComfyUI"}),
                "filename_prefix": ("STRING", {"default": "comfy"}),
            }
        }

    def save_images(self, images, base_url, username, password, remote_path, filename_prefix):
        remote_folder_url = _ensure_remote_directory(base_url, username, password, remote_path)
        auth_header = _build_auth_header(username, password)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

        uploaded_files = []
        previews = []
        for index, image in enumerate(images):
            file_name = f"{filename_prefix}_{timestamp}_{index:04d}.png"
            upload_url = f"{remote_folder_url}/{parse.quote(file_name, safe='')}"

            pil_image = _tensor_to_image(image)

            payload = _image_to_png_bytes(pil_image)
            _upload_file(upload_url, auth_header, payload)
            uploaded_files.append(file_name)

            preview = _save_preview_file(file_name, pil_image)
            if preview is not None:
                previews.append(preview)

        return {
            "ui": {
                "images": previews,
                "text": [
                    f"Uploaded {len(uploaded_files)} file(s) to {remote_folder_url}",
                    *uploaded_files,
                ]
            }
        }


NODE_CLASS_MAPPINGS = {
    "SaveImageToNextcloud": SaveImageToNextcloud,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageToNextcloud": "Save Image To Nextcloud",
}
