from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import re
from janis_core3.opensearch_client import get_opensearch_client
from django.apps import apps
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField
from django.db.models import TextField, CharField


def strip_tags(html: str) -> str:
    # simple tag stripper
    return re.sub(r'<[^>]+>', ' ', html)


class Command(BaseCommand):
    help = 'Index templates (HTML) into OpenSearch index site_search'

    def handle(self, *args, **options):
        templates_dir = Path(settings.BASE_DIR) / 'templates'
        client = get_opensearch_client()
        index = 'site_search'

        # create index if not exists
        if not client.indices.exists(index=index):
            mapping = {
                'mappings': {
                    'properties': {
                        'title': {'type': 'text'},
                        'body': {'type': 'text'},
                        'url': {'type': 'keyword'},
                        'type': {'type': 'keyword'},
                        'thumbnail': {'type': 'keyword'},
                        'snippet': {'type': 'text'}
                    }
                }
            }
            client.indices.create(index=index, body=mapping)
            self.stdout.write(self.style.SUCCESS(f'Index {index} created'))

        count = 0
        for f in templates_dir.rglob('*.html'):
            try:
                text = f.read_text(encoding='utf-8')
            except Exception:
                continue
            title_match = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else f.name
            body = strip_tags(text)
            snippet = body[:400]
            # derive a pseudo-url from path relative to templates_dir
            rel = f.relative_to(templates_dir).as_posix()
            url = f'/{rel}'
            doc = {
                'title': title,
                'body': body,
                'url': url,
                'type': 'template',
                'thumbnail': None,
                'snippet': snippet,
            }
            client.index(index=index, body=doc, id=f'{rel}')
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Indexed {count} templates into {index}'))

        # Index model instances for key models (Properties, Requirements)
        model_docs = 0
        try:
            Property = apps.get_model('properties', 'Property')
            Requirement = apps.get_model('properties', 'Requirement')
        except Exception:
            Property = None
            Requirement = None

        def gather_text_from_instance(inst):
            parts = []
            model_name = getattr(inst._meta, 'model_name', '').lower()
            for field in inst._meta.get_fields():
                # only simple fields (no relations) and text/char types
                try:
                    f = inst._meta.get_field(field.name)
                except Exception:
                    continue
                # Special-case: for Requirement include `notes` even if encrypted (decrypted by field)
                if model_name == 'requirement' and f.name == 'notes':
                    try:
                        val = getattr(inst, f.name, '') or ''
                        if isinstance(val, str):
                            parts.append(val)
                    except Exception:
                        pass
                    continue
                # skip encrypted fields for privacy by default
                if isinstance(f, (EncryptedCharField, EncryptedTextField)):
                    continue
                if isinstance(f, (CharField, TextField)):
                    val = getattr(inst, f.name, '') or ''
                    if isinstance(val, str):
                        parts.append(val)
            return ' '.join(parts)

        if Property:
            qs = Property.objects.all()[:5000]
            for p in qs:
                try:
                    title = p.title or p.code or f'Property {p.pk}'
                    body = gather_text_from_instance(p)
                    snippet = (body or '')[:400]
                    thumb = None
                    try:
                        if hasattr(p, 'images') and p.images.exists():
                            img = p.images.first()
                            thumb = getattr(img.image, 'url', None)
                    except Exception:
                        thumb = None
                    doc = {
                        'title': title,
                        'body': body,
                        'url': f'/properties/{p.pk}/',
                        'type': 'property',
                        'thumbnail': thumb,
                        'snippet': snippet,
                    }
                    client.index(index=index, body=doc, id=f'property_{p.pk}')
                    model_docs += 1
                except Exception:
                    continue

        if Requirement:
            qs = Requirement.objects.all()[:5000]
            for r in qs:
                try:
                    title = f'Requerimiento {r.pk}'
                    # avoid indexing PII: gather only non-encrypted textual fields
                    body = gather_text_from_instance(r)
                    snippet = (body or '')[:400]
                    doc = {
                        'title': title,
                        'body': body,
                        'url': f'/requirements/{r.pk}/',
                        'type': 'requirement',
                        'thumbnail': None,
                        'snippet': snippet,
                    }
                    client.index(index=index, body=doc, id=f'requirement_{r.pk}')
                    model_docs += 1
                except Exception:
                    continue

        self.stdout.write(self.style.SUCCESS(f'Indexed {model_docs} model instances into {index}'))
