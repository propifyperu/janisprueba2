from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Case, When, Value, IntegerField
from .models import Property, District, Province, Department
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
        fields = tuple(f for f in PropertySerializer.Meta.fields if f not in ['images', 'videos', 'documents', 'owner', 'responsible_name', 'financial_info'])

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
            
            # [MEJORA 1] Pre-análisis: Detectar frases de ubicación exactas y números ANTES de limpiar/separar
            exact_location_ids = {'dist': [], 'prov': [], 'dept': []}
            exact_location_names = {'dist': [], 'prov': [], 'dept': []}
            numeric_criteria = []

            if isinstance(keywords, list):
                for k in keywords:
                    phrase = str(k).strip()
                    # Detectar números (para habitaciones o precio)
                    if re.match(r'^\d+$', phrase):
                        numeric_criteria.append(int(phrase))
                    
                    # Detectar ubicaciones compuestas exactas (ej: "Cerro Colorado", "Jose Luis Bustamante")
                    dists = District.objects.filter(name__iexact=phrase).values('id', 'name')
                    for d in dists:
                        exact_location_ids['dist'].append(str(d['id']))
                        exact_location_names['dist'].append(d['name'])
                    
                    provs = Province.objects.filter(name__iexact=phrase).values('id', 'name')
                    for p in provs:
                        exact_location_ids['prov'].append(str(p['id']))
                        exact_location_names['prov'].append(p['name'])

                    depts = Department.objects.filter(name__iexact=phrase).values('id', 'name')
                    for d in depts:
                        exact_location_ids['dept'].append(str(d['id']))
                        exact_location_names['dept'].append(d['name'])

            if isinstance(keywords, list): # limpieza avanzada: separar por espacios y eliminar stopwords (artículos, pronombres)
                processed_keywords = []
                STOPWORDS = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'y', 'o', 'en', 'con', 'por'}
                for k in keywords:
                    
                    words = str(k).split() # separar frases por espacios (ej: "urbanizacion terrazas" -> ["urbanizacion", "terrazas"])
                    for w in words:
                        clean_w = w.strip().strip('"\'.,')
                        if clean_w and clean_w.lower() not in STOPWORDS:
                            processed_keywords.append(clean_w)
                            
                            # [MEJORA 4] Detectar ubicación/números también en palabras sueltas (ej: "sachaca" dentro de "casa en sachaca")
                            phrase = clean_w
                            if re.match(r'^\d+$', phrase):
                                numeric_criteria.append(int(phrase))

                            dists = District.objects.filter(name__iexact=phrase).values('id', 'name')
                            for d in dists:
                                exact_location_ids['dist'].append(str(d['id']))
                                exact_location_names['dist'].append(d['name'])
                            
                            provs = Province.objects.filter(name__iexact=phrase).values('id', 'name')
                            for p in provs:
                                exact_location_ids['prov'].append(str(p['id']))
                                exact_location_names['prov'].append(p['name'])

                            depts = Department.objects.filter(name__iexact=phrase).values('id', 'name')
                            for d in depts:
                                exact_location_ids['dept'].append(str(d['id']))
                                exact_location_names['dept'].append(d['name'])

                keywords = processed_keywords

            if isinstance(user_ids, str):
                user_ids = user_ids.strip('[]')
                user_ids = [uid.strip().strip('"\'') for uid in user_ids.split(',') if uid.strip()]
            
            if not keywords or not isinstance(keywords, list):
                return Response([])

            score = Value(0, output_field=IntegerField())
            
            # Deduplicar criterios numéricos para evitar puntaje doble
            numeric_criteria = list(set(numeric_criteria))
            
            # Deduplicar ubicaciones
            for key in exact_location_ids:
                exact_location_ids[key] = list(set(exact_location_ids[key]))
                exact_location_names[key] = list(set(exact_location_names[key]))

            # [MEJORA 2] Aplicar puntaje alto por coincidencia de frase de ubicación exacta
            # Aumentamos drásticamente los puntajes (10,000) para asegurar que el distrito sea lo más importante.
            if exact_location_ids['dist']:
                score = score + Case(When(district__in=exact_location_ids['dist'], then=Value(10000)), default=Value(0), output_field=IntegerField())
            
            for dist_name in exact_location_names['dist']:
                score = score + Case(When(district__iexact=dist_name, then=Value(10000)), default=Value(0), output_field=IntegerField())

            if exact_location_ids['prov']:
                score = score + Case(When(province__in=exact_location_ids['prov'], then=Value(5000)), default=Value(0), output_field=IntegerField())
            
            for prov_name in exact_location_names['prov']:
                score = score + Case(When(province__iexact=prov_name, then=Value(5000)), default=Value(0), output_field=IntegerField())

            if exact_location_ids['dept']:
                score = score + Case(When(department__in=exact_location_ids['dept'], then=Value(2000)), default=Value(0), output_field=IntegerField())
            
            for dept_name in exact_location_names['dept']:
                score = score + Case(When(department__iexact=dept_name, then=Value(2000)), default=Value(0), output_field=IntegerField())
            
            # [MEJORA 3] Aplicar puntaje por coincidencias numéricas (Habitaciones / Precio)
            for num in numeric_criteria:
                if 1 <= num <= 10: # Asumimos habitaciones/baños si es número bajo
                    score = score + Case(When(bedrooms=num, then=Value(20)), default=Value(0), output_field=IntegerField())
                    score = score + Case(When(bathrooms=num, then=Value(10)), default=Value(0), output_field=IntegerField())
                elif num > 1000: # Asumimos precio si es alto (margen +/- 10%)
                    min_p = num * 0.9
                    max_p = num * 1.1
                    score = score + Case(When(price__gte=min_p, price__lte=max_p, then=Value(25)), default=Value(0), output_field=IntegerField())

            for idx, word in enumerate(keywords):
                word = str(word).strip()
                if not word: continue
                
                
                multiplier = 3 if idx == 0 else (2 if idx == 1 else 1) # importancia por orden: 1ra palabra (x3), 2da (x2), resto (x1)
                
                # Buscar IDs si la palabra corresponde a un lugar (para campos que guardan ID como string)
                dist_ids = [str(x) for x in District.objects.filter(name__icontains=word).values_list('id', flat=True)]
                prov_ids = [str(x) for x in Province.objects.filter(name__icontains=word).values_list('id', flat=True)]
                dept_ids = [str(x) for x in Department.objects.filter(name__icontains=word).values_list('id', flat=True)]

                # asignacion de pesos: código (20 pts), dirección (15 pts), título (10 pts), amenities (5 pts), descripción (2 pt)
                score = score + \
                    Case(When(code__icontains=word, then=Value(20 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(code__iexact=word, then=Value(30 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(title__iexact=word, then=Value(20 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(district__iexact=word, then=Value(20 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(property_type__name__iexact=word, then=Value(20 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(exact_address__icontains=word, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(real_address__icontains=word, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(urbanization__icontains=word, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(title__icontains=word, then=Value(10 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(property_type__name__icontains=word, then=Value(10 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(property_subtype__name__icontains=word, then=Value(10 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(amenities__icontains=word, then=Value(5 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(description__icontains=word, then=Value(2 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(district__icontains=word, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(province__icontains=word, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField()) + \
                    Case(When(department__icontains=word, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField())

                # Agregar coincidencia por ID de ubicación
                if dist_ids:
                    score = score + Case(When(district__in=dist_ids, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField())
                if prov_ids:
                    score = score + Case(When(province__in=prov_ids, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField())
                if dept_ids:
                    score = score + Case(When(department__in=dept_ids, then=Value(15 * multiplier)), default=Value(0), output_field=IntegerField())

            
            results = [] # intentar filtrar por usuarios si se proporcionaron
            if user_ids:
                qs = Property.objects.filter(is_active=True, created_by_id__in=user_ids)
                qs = qs.annotate(match_score=score).filter(match_score__gt=0).order_by('-match_score').distinct()[:5]
                results = list(qs)

            # Fallback global inteligente:
            # Si no hay resultados, O si los resultados encontrados no son "perfectos" (score < 2000),
            # buscamos en toda la base de datos. Esto permite que si la búsqueda local encontró solo "Casa" (score bajo)
            # pero globalmente existe "Casa en Sachaca" (score alto por ubicación), el sistema prefiera la mejor coincidencia.
            if not results or (results and getattr(results[0], 'match_score', 0) < 2000):
                qs = Property.objects.filter(is_active=True)
                qs = qs.annotate(match_score=score).filter(match_score__gt=0).order_by('-match_score').distinct()[:5]
                global_results = list(qs)
                
                
                if global_results and (not results or getattr(global_results[0], 'match_score', 0) > getattr(results[0], 'match_score', 0)): # Si la búsqueda global trajo mejores resultados (o los únicos), usarlos
                    results = global_results

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