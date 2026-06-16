from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Sum
from django.core.cache import cache

from .models import Order, OrderItem, OrderStatus
from .serializers import OrderCreationSerializer, OrderResponseSerializer, OrderListSerializer
from apps.stores.models import Inventory, Store
from .tasks import send_order_confirmation

class OrderCreateView(APIView):
    def post(self, request):
        serializer = OrderCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        store_id = serializer.validated_data['store_id']
        items_data = serializer.validated_data['items']

        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND)

        product_ids = [item['product_id'] for item in items_data]
        quantities = {item['product_id']: item['quantity_requested'] for item in items_data}

        with transaction.atomic():
            # select_for_update to lock the inventory rows during this transaction
            inventory_qs = Inventory.objects.select_for_update().filter(
                store_id=store_id, 
                product_id__in=product_ids
            )
            
            inventory_map = {inv.product_id: inv for inv in inventory_qs}

            # Check for missing products in inventory
            if len(inventory_map) != len(product_ids):
                # Order rejected due to missing products
                order = Order.objects.create(store=store, status=OrderStatus.REJECTED)
                return Response(
                    OrderResponseSerializer(order).data,
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check stock
            sufficient_stock = True
            for pid, requested_qty in quantities.items():
                if inventory_map[pid].quantity < requested_qty:
                    sufficient_stock = False
                    break

            if not sufficient_stock:
                order = Order.objects.create(store=store, status=OrderStatus.REJECTED)
            else:
                # Deduct stock
                for pid, requested_qty in quantities.items():
                    inv = inventory_map[pid]
                    inv.quantity -= requested_qty
                    inv.save()
                
                order = Order.objects.create(store=store, status=OrderStatus.CONFIRMED)
                
                # Invalidate entire cache to clear the inventory list
                # (In a real system, we'd clear specifically the key for this store's inventory)
                cache.clear()

                # Trigger Celery Task
                send_order_confirmation.delay(order.id)

            # Create order items regardless of status for record keeping
            order_items = []
            for pid, requested_qty in quantities.items():
                order_items.append(OrderItem(
                    order=order,
                    product_id=pid,
                    quantity_requested=requested_qty
                ))
            OrderItem.objects.bulk_create(order_items)

        return Response(OrderResponseSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer

    def get_queryset(self):
        store_id = self.kwargs.get('store_id')
        # Annotate with sum of requested quantities, default to 0 if no items
        return Order.objects.filter(store_id=store_id).annotate(
            total_items=Sum('items__quantity_requested')
        ).order_by('-created_at')
