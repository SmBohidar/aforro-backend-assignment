from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, F, Subquery, OuterRef, Case, When, Value, IntegerField
from django_filters import rest_framework as filters

from apps.products.models import Product
from apps.stores.models import Inventory
from rest_framework import serializers

class DynamicProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    store_quantity = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'category_name', 'store_quantity']

class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category__name', lookup_expr='iexact')
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')
    
    class Meta:
        model = Product
        fields = ['category']

class ProductSearchAPIView(generics.ListAPIView):
    serializer_class = DynamicProductSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        qs = Product.objects.select_related('category')
        
        q = self.request.query_params.get('q', '')
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(category__name__icontains=q)
            )

        store_id = self.request.query_params.get('store_id')
        in_stock = self.request.query_params.get('in_stock')

        if store_id:
            # Annotate with inventory quantity for this specific store
            inventory_subquery = Inventory.objects.filter(
                product=OuterRef('pk'), 
                store_id=store_id
            ).values('quantity')[:1]
            
            qs = qs.annotate(store_quantity=Subquery(inventory_subquery))
            
            if in_stock and in_stock.lower() == 'true':
                qs = qs.filter(store_quantity__gt=0)
        else:
            if in_stock and in_stock.lower() == 'true':
                qs = qs.filter(inventory_records__quantity__gt=0).distinct()

        sort = self.request.query_params.get('sort', 'relevance')
        if sort == 'price':
            qs = qs.order_by('price')
        elif sort == '-price':
            qs = qs.order_by('-price')
        elif sort == 'newest':
            qs = qs.order_by('-id')
        elif sort == 'relevance' and q:
            qs = qs.annotate(
                relevance=Case(
                    When(title__iexact=q, then=Value(3)),
                    When(title__istartswith=q, then=Value(2)),
                    When(title__icontains=q, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-relevance', 'title')
            
        return qs

class AutocompleteAPIView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 3:
            return Response([])

        qs = Product.objects.filter(title__icontains=q).annotate(
            is_prefix=Case(
                When(title__istartswith=q, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-is_prefix', 'title')[:10]

        results = [{"title": p.title} for p in qs]
        return Response(results)
