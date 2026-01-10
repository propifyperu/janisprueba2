from django.conf import settings
from opensearchpy import OpenSearch

_client = None

def get_opensearch_client():
    """Return a cached OpenSearch client configured from settings.OPENSEARCH_HOSTS."""
    global _client
    if _client is None:
        hosts = getattr(settings, 'OPENSEARCH_HOSTS', ['http://localhost:9200'])
        # hosts should be list of URLs
        _client = OpenSearch(hosts)
    return _client
