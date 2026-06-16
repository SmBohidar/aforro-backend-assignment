from django.db import models
from apps.products.models import Product

class Store(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Inventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="inventory_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_records")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Inventories"
        constraints = [
            models.UniqueConstraint(fields=['store', 'product'], name='unique_store_product_inventory')
        ]

    def __str__(self):
        return f"{self.store.name} - {self.product.title}: {self.quantity}"
