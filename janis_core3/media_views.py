from django.http import StreamingHttpResponse, Http404
from django.views.decorators.http import require_GET
from django.conf import settings

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def _get_blob_client(name):
    account_name = getattr(settings, 'AZURE_ACCOUNT_NAME', None)
    account_key = getattr(settings, 'AZURE_ACCOUNT_KEY', None)
    container = getattr(settings, 'AZURE_CONTAINER', 'media')

    if account_name and not account_key:
        credential = DefaultAzureCredential()
        endpoint = f"https://{account_name}.blob.core.windows.net"
        client = BlobServiceClient(account_url=endpoint, credential=credential)
    elif account_name and account_key:
        endpoint = f"https://{account_name}.blob.core.windows.net"
        client = BlobServiceClient(account_url=endpoint, credential=account_key)
    else:
        raise RuntimeError('Azure storage not configured')

    return client.get_blob_client(container=container, blob=name)


@require_GET
def media_proxy(request, path):
    """Stream a blob from private container to the client using MSI or account key."""
    blob_client = _get_blob_client(path)
    try:
        stream = blob_client.download_blob()
    except Exception:
        raise Http404()

    response = StreamingHttpResponse(stream.chunks(), content_type=stream.properties.content_settings.content_type)
    response['Content-Length'] = stream.properties.size
    return response
