# comfy-nextcloud-save

ComfyUI custom node that saves generated images to Nextcloud via WebDAV.

## Install

Clone this repository into `ComfyUI/custom_nodes` and restart ComfyUI.

## Node

`Save Image To Nextcloud`

Inputs:

- `images`: ComfyUI image batch
- `base_url`: Nextcloud base URL, for example `https://cloud.example.com`
- `username`: Nextcloud username
- `password`: Nextcloud password or app password
- `remote_path`: Destination folder under the user's files, for example `Photos/ComfyUI`
- `filename_prefix`: Prefix used for uploaded PNG filenames

The node creates missing folders and uploads each image as PNG using the Nextcloud WebDAV endpoint.
