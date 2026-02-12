from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Case, When, Value, IntegerField
from .models import Property
from .serializers import PropertySerializer

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

    def post(self, request, *args, **kwargs):
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