import logging
from celery import shared_task
from .models import Order

logger = logging.getLogger(__name__)

@shared_task
def send_order_confirmation(order_id):
    """
    Simulates sending an order confirmation asynchronously.
    """
    try:
        order = Order.objects.get(id=order_id)
        logger.info(f"CELERY TASK: Sending confirmation for Order #{order.id} (Status: {order.status})")
        return f"Order {order_id} confirmation sent successfully."
    except Order.DoesNotExist:
        logger.error(f"CELERY TASK: Order #{order_id} not found.")
        return f"Order {order_id} not found."
