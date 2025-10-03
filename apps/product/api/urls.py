from django.urls import path 
from .views import *
urlpatterns = [
    # category endpoints
    path('categories/',CategoryListView.as_view(), name = 'category_list' ),
    path('categories/<int:pk>/',CategoryDetailView.as_view(), name = 'category_details' ),
    path('categories/create/',CategoryCreateView.as_view(), name = 'create_category'),
    path('categories/update/<int:pk>/',CategoryUpdateView.as_view(), name = 'update_category'),
    path('categories/delete/<int:pk>/',CategoryDeleteView.as_view(), name = 'delete_category'),
    # product endpoints
    path('products/',ProductCreateListView.as_view(), name = 'product_list_create' ),
]
