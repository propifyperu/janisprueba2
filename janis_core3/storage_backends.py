from io import BytesIO
from urllib.parse import quote

from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.encoding import filepath_to_uri

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class AzureManagedIdentityStorage(Storage):
    """Storage backend that uploads to Azure Blob using Managed Identity / DefaultAzureCredential.

    - Uploads and deletes blobs via `BlobServiceClient` using `DefaultAzureCredential` when available.
    - Returns internal proxy URL (`/media-proxy/<name>`) so Django serves files through a secure view
      that uses the same credential to stream blobs (no public access, no account keys in code).
    """

    def __init__(self):
        self.account_name = getattr(settings, 'AZURE_ACCOUNT_NAME', None)
        self.account_key = getattr(settings, 'AZURE_ACCOUNT_KEY', None)
        self.container = getattr(settings, 'AZURE_CONTAINER', 'media')

        # Prefer DefaultAzureCredential (Managed Identity) but fall back to account key
        if self.account_name and not self.account_key:
            credential = DefaultAzureCredential()
            endpoint = f"https://{self.account_name}.blob.core.windows.net"
            self.client = BlobServiceClient(account_url=endpoint, credential=credential)
        elif self.account_name and self.account_key:
            # fallback for environments without MSI (still secure if using App Settings)
            connection_string = None
            endpoint = f"https://{self.account_name}.blob.core.windows.net"
            self.client = BlobServiceClient(account_url=endpoint, credential=self.account_key)
        else:
            self.client = None

    def _get_blob_client(self, name):
        if not self.client:
            raise RuntimeError('Azure storage client not configured')
        return self.client.get_blob_client(container=self.container, blob=name)

    def _save(self, name, content):
        # content may be File or ContentFile; ensure bytes
        blob = self._get_blob_client(name)
        data = content.read() if hasattr(content, 'read') else content
        if isinstance(data, str):
            data = data.encode('utf-8')
        blob.upload_blob(data, overwrite=True)
        return name

    def save(self, name, content):
        return self._save(name, content)

    def exists(self, name):
        try:
            blob = self._get_blob_client(name)
            return blob.exists()
        except Exception:
            return False

    def url(self, name):
        # Return internal proxy path; view will stream blob using MSI
        quoted = filepath_to_uri(name)
        return f"/media-proxy/{quoted}"

    def delete(self, name):
        try:
            blob = self._get_blob_client(name)
            blob.delete_blob()
        except Exception:
            pass

    def size(self, name):
        blob = self._get_blob_client(name)
        props = blob.get_blob_properties()
        return props.size

