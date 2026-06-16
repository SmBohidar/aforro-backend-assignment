from django.urls import path
from .views import ProductSearchAPIView, AutocompleteAPIView

urlpatterns = [
    path('products/', ProductSearchAPIView.as_view(), name='product-search'),
    path('suggest/', AutocompleteAPIView.as_view(), name='autocomplete'),
]
