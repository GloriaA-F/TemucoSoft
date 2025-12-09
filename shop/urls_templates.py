from django.urls import path
from . import views_templates

urlpatterns = [
    # Auth
    path('login/', views_templates.login_view, name='login'),
    path('logout/', views_templates.logout_view, name='logout'),
    
    # Dashboard
    path('', views_templates.dashboard, name='dashboard'),
    path('dashboard/', views_templates.dashboard, name='dashboard'),
    
    # Products
    path('products/', views_templates.product_list, name='product_list'),
    path('products/create/', views_templates.product_create, name='product_create'),
    path('products/<int:pk>/', views_templates.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views_templates.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views_templates.product_delete, name='product_delete'),
    
    # Suppliers
    path('suppliers/', views_templates.supplier_list, name='supplier_list'),
    path('suppliers/create/', views_templates.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views_templates.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views_templates.supplier_delete, name='supplier_delete'),
    
    # Branches
    path('branches/', views_templates.branch_list, name='branch_list'),
    path('branches/create/', views_templates.branch_create, name='branch_create'),
    path('branches/<int:pk>/edit/', views_templates.branch_edit, name='branch_edit'),
    path('branches/<int:pk>/delete/', views_templates.branch_delete, name='branch_delete'),
    
    # Inventory
    path('inventory/', views_templates.inventory_list, name='inventory_list'),
    path('inventory/adjust/', views_templates.inventory_adjust, name='inventory_adjust'),
    
    # Sales
    path('sales/', views_templates.sale_list, name='sale_list'),
    path('sales/create/', views_templates.sale_create, name='sale_create'),
    path('sales/<int:pk>/', views_templates.sale_detail, name='sale_detail'),
    path('sales/add-item/', views_templates.sale_add_item, name='sale_add_item'),
    path('sales/remove-item/<int:product_id>/', views_templates.sale_remove_item, name='sale_remove_item'),
    
    # Shop/Catalog
    path('catalog/', views_templates.shop_catalog, name='shop_catalog'),
    path('catalog/<int:pk>/', views_templates.shop_product_detail, name='shop_product_detail'),
    
    # Reports
    path('reports/sales/', views_templates.reports_sales, name='reports_sales'),
    path('reports/stock/', views_templates.reports_stock, name='reports_stock'),
]
