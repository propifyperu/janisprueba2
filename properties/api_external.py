from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Case, When, Value, IntegerField
from .models import Property
from .serializers import PropertySerializer
from rest_framework.parsers import JSONParser
import json
import re

class ForgivingJSONParser(JSONParser):
    """
    Parser que intenta corregir JSON malformado (ej: faltan comillas en listas).
    """
    def parse(self, stream, media_type=None, parser_context=None):
        content = stream.read().decode(parser_context.get('encoding', 'utf-8'))
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            
            fixed = re.sub(r'(?<=\{|\,)\s*([a-zA-Z0-9_]+)\s*:', r'"\1":', content) # corregir claves sin comillas: { key: -> {"key":
            
            
            def fix_value(match): # corregir valores string sin comillas
                val = match.group(1)
                if val in ('true', 'false', 'null') or re.match(r'^-?\d+(\.\d+)?$', val):
                    return match.group(0)
                return f'"{val}"'

            fixed = re.sub(r'(?<=[:\[,])\s*([a-zA-Z0-9_\u00C0-\u00FF]+)\s*(?=[,\]\}])', fix_value, fixed)
            
            try:
                return json.loads(fixed)
            except Exception:
                return {}

class ExternalPropertySerializer(PropertySerializer):
    class Meta(PropertySerializer.Meta):
        fields = tuple(f for f in PropertySerializer.Meta.fields if f not in ['images', 'videos', 'documents'])

class ExternalPropertyListView(ListAPIView):
    serializer_class = ExternalPropertySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['province', 'district', 'property_type', 'status', 'currency']
    search_fields = ['title', 'description', 'code']
    ordering_fields = ['price', 'created_at', 'updated_at']

    def get_queryset(self):
        return Property.objects.filter(is_active=True).select_related(
            'currency', 'property_type', 'status', 'owner'
        ).order_by('-created_at')

class ExternalPropertyMatchView(APIView):
    """
    {"keywords": ["piscina", "playa", "asia"], "user_ids": [1, 5]}, solo devuelve 3
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [ForgivingJSONParser]

    def post(self, request, *args, **kwargs):
        print(f"\n=== DEBUG EXTERNO PAYLOAD ===")
        try:
            print(f"Data recibida: {request.data}")
        except Exception as e:
            print(f"Error leyendo data: {e}")
        print(f"=========================\n")

        try:
            data = request.data
            keywords = []
            user_ids = []

            if isinstance(data, list):
                keywords = data
            else:
                keywords = data.get('keywords', [])
                user_ids = data.get('user_ids', [])
            
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            
            # Robustez: Aplanar lista si viene anidada (ej: n8n envía [["a", "b"]] por doble corchete)
            if isinstance(keywords, list):
                flat_keywords = []
                for item in keywords:
                    if isinstance(item, list):
                        flat_keywords.extend(item)
                    else:
                        flat_keywords.append(item)
                keywords = flat_keywords

            if isinstance(user_ids, str):
                user_ids = [uid.strip() for uid in user_ids.split(',') if uid.strip()]
            
            if not keywords or not isinstance(keywords, list):
                return Response([])

            qs = Property.objects.filter(is_active=True)

            if user_ids:
                qs = qs.filter(created_by_id__in=user_ids)

            score = Value(0, output_field=IntegerField())

            for word in keywords:
                word = str(word).strip()
                if not word: continue
                
                # asignacion de pesos: código (10 pts), título (5 pts), dirección (3 pts), amenities (2 pts), descripción (1 pt)
                score = score + \
                    Case(When(code__icontains=word, then=Value(10)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(title__icontains=word, then=Value(5)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(exact_address__icontains=word, then=Value(3)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(amenities__icontains=word, then=Value(2)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(description__icontains=word, then=Value(1)), default=Value(0), output_field=IntegerField())

            qs = qs.annotate(match_score=score).filter(match_score__gt=0).order_by('-match_score')[:3]

            serializer = ExternalPropertySerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            print(f"ERROR INTERNO: {e}")
            return Response({"error": str(e)}, status=500)