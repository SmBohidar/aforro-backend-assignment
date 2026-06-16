import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from faker import Faker

from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory
from apps.orders.models import Order, OrderItem

class Command(BaseCommand):
    help = 'Seeds the database with dummy data for categories, products, stores, and inventory.'

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        self.stdout.write(self.style.WARNING('Clearing existing data...'))
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Inventory.objects.all().delete()
        Store.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(self.style.WARNING('Generating Categories (15)...'))
        categories = []
        for _ in range(15):
            cat = Category(name=fake.company() + " " + fake.word().capitalize())
            categories.append(cat)
        Category.objects.bulk_create(categories)
        categories = list(Category.objects.all())

        self.stdout.write(self.style.WARNING('Generating Products (1200)...'))
        products = []
        for _ in range(1200):
            product = Product(
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=200),
                price=Decimal(random.uniform(5.0, 500.0)).quantize(Decimal('0.01')),
                category=random.choice(categories)
            )
            products.append(product)
        Product.objects.bulk_create(products, batch_size=500)
        all_products = list(Product.objects.all())

        self.stdout.write(self.style.WARNING('Generating Stores (25)...'))
        stores = []
        for _ in range(25):
            store = Store(
                name=fake.company(),
                location=fake.address().replace('\n', ', ')
            )
            stores.append(store)
        Store.objects.bulk_create(stores)
        all_stores = list(Store.objects.all())

        self.stdout.write(self.style.WARNING('Generating Inventory for Stores...'))
        inventories = []
        for store in all_stores:
            # Randomly select between 300 and 400 unique products for this store
            num_products = random.randint(300, 400)
            store_products = random.sample(all_products, num_products)
            
            for product in store_products:
                inventories.append(Inventory(
                    store=store,
                    product=product,
                    quantity=random.randint(10, 500)
                ))
                
        # Bulk create in batches
        Inventory.objects.bulk_create(inventories, batch_size=1000)

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with dummy data!'))
