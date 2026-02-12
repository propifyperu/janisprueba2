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

def forgiving_json_loads(content):
    """Intenta cargar JSON y si falla aplica correcciones regex (comillas faltantes)."""
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

class ForgivingJSONParser(JSONParser):
    """
    Parser que intenta corregir JSON malformado (ej: faltan comillas en listas).
    """
    def parse(self, stream, media_type=None, parser_context=None):
        content = stream.read().decode(parser_context.get('encoding', 'utf-8'))
        return forgiving_json_loads(content)

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
        try:
            data = request.data
            
            if isinstance(data, str):
                data = forgiving_json_loads(data)

            keywords = []
            user_ids = []

            if isinstance(data, list):
                keywords = data
            elif isinstance(data, dict):
                keywords = data.get('keywords', [])
                user_ids = data.get('user_ids', [])
            
            if isinstance(keywords, str):
                # Intentar parsear como JSON primero (maneja comillas y comas internas)
                parsed = None
                if keywords.strip().startswith('['):
                    parsed = forgiving_json_loads(keywords)
                
                if isinstance(parsed, list):
                    keywords = parsed
                else:
                    
                    keywords = keywords.strip('[]') # csv manual, eliminando corchetes y comillas
                    keywords = [k.strip().strip('"\'') for k in keywords.split(',') if k.strip()]
            
            if isinstance(keywords, list): # robustez: Aplanar lista si viene anidada (ej: n8n envía [["a", "b"]] por doble corchete)
                flat_keywords = []
                for item in keywords:
                    if isinstance(item, list):
                        flat_keywords.extend(item)
                    else:
                        flat_keywords.append(item)
                keywords = flat_keywords

            if isinstance(user_ids, str):
                user_ids = user_ids.strip('[]')
                user_ids = [uid.strip().strip('"\'') for uid in user_ids.split(',') if uid.strip()]
            
            if not keywords or not isinstance(keywords, list):
                return Response([])

            score = Value(0, output_field=IntegerField())

            for word in keywords:
                word = str(word).strip()
                if not word: continue
                
                # asignacion de pesos: código (20 pts), dirección (15 pts), título (10 pts), amenities (5 pts), descripción (2 pt)
                score = score + \
                    Case(When(code__icontains=word, then=Value(20)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(exact_address__icontains=word, then=Value(15)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(real_address__icontains=word, then=Value(15)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(urbanization__icontains=word, then=Value(15)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(title__icontains=word, then=Value(10)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(amenities__icontains=word, then=Value(5)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(description__icontains=word, then=Value(2)), default=Value(0), output_field=IntegerField())

            
            results = [] # intentar filtrar por usuarios si se proporcionaron
            if user_ids:
                qs = Property.objects.filter(is_active=True, created_by_id__in=user_ids)
                qs = qs.annotate(match_score=score).filter(match_score__gt=0).order_by('-match_score')[:3]
                results = list(qs)

            
            if not results: # fallback global si no hay resultados (o no se filtró por usuario)
                qs = Property.objects.filter(is_active=True)
                qs = qs.annotate(match_score=score).filter(match_score__gt=0).order_by('-match_score')[:3]
                results = list(qs)

            serializer = ExternalPropertySerializer(results, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ExternalPropertyByUsersView(APIView):
    """
    Endpoint externo para obtener TODAS las propiedades de una lista de usuarios.
    Método: POST
    Body: {"user_ids": [2, 7, 1]}
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [ForgivingJSONParser]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            
            if isinstance(data, str):
                data = forgiving_json_loads(data)

            user_ids = []

            if isinstance(data, dict):
                user_ids = data.get('user_ids', [])
            
            if isinstance(user_ids, str):
                user_ids = user_ids.strip('[]')
                user_ids = [uid.strip().strip('"\'') for uid in user_ids.split(',') if uid.strip()]
            
            if isinstance(user_ids, list):
                flat_ids = []
                for item in user_ids:
                    if isinstance(item, list):
                        flat_ids.extend(item)
                    else:
                        flat_ids.append(item)
                user_ids = flat_ids

            if not user_ids:
                return Response([])

            
            qs = Property.objects.filter(is_active=True, created_by_id__in=user_ids).order_by('-created_at') # devolver todas las propiedades activas de estos usuarios
            
            serializer = ExternalPropertySerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)