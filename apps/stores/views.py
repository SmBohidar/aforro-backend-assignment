from rest_framework import generics
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from apps.stores.models import Inventory
from apps.stores.serializers import InventorySerializer

class InventoryListView(generics.ListAPIView):
    serializer_class = InventorySerializer

    # Cache for 15 minutes to fulfill Option A (Redis Caching)
    @method_decorator(cache_page(60 * 15))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        store_id = self.kwargs.get('store_id')
        # select_related to avoid N+1 queries on product and category
        return Inventory.objects.filter(store_id=store_id).select_related(
            'product', 'product__category'
        ).order_by('product__title')
