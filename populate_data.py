#!/usr/bin/env python
import os
import django
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temucosoft_project.settings')
django.setup()

from core.models import User, Company, Subscription
from products.models import Product, Supplier, Category
from inventory.models import Branch, Inventory
from sales.models import Sale, SaleItem

def create_data():
    print("🚀 Iniciando población de datos de prueba...\n")
    
    # 1. Crear Empresa
    print("📦 Creando empresa...")
    company, created = Company.objects.get_or_create(
        rut='76123456-7',
        defaults={
            'name': 'Minimarket Don Pepe',
            'contact_email': 'contacto@donpepe.cl',
            'contact_phone': '+56912345678',
            'address': 'Av. Alemania 685, Temuco',
            'is_active': True
        }
    )
    print(f"   ✓ Empresa: {company.name}")
    
    # 2. Crear Suscripción
    print("\n💳 Creando suscripción...")
    subscription, created = Subscription.objects.get_or_create(
        company=company,
        defaults={
            'plan_name': 'premium',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365),
            'active': True,
            'max_branches': 5,
            'max_users': 20
        }
    )
    print(f"   ✓ Plan: {subscription.get_plan_name_display()}")
    
    # 3. Crear Usuarios
    print("\n👥 Creando usuarios...")
    
    # Admin ya existe, solo actualizar su company
    admin = User.objects.get(username='admin')
    admin.company = company
    admin.first_name = 'Super'
    admin.last_name = 'Admin'
    admin.save()
    print(f"   ✓ Super Admin actualizado")
    
    # Admin Cliente
    admin_cliente, created = User.objects.get_or_create(
        username='admin_donpepe',
        defaults={
            'email': 'admin@donpepe.cl',
            'rut': '12345678-5',
            'role': 'admin_cliente',
            'company': company,
            'first_name': 'Pedro',
            'last_name': 'González',
            'is_active': True
        }
    )
    if created:
        admin_cliente.set_password('Admin123!')
        admin_cliente.save()
    print(f"   ✓ Admin Cliente: {admin_cliente.username} / Admin123!")
    
    # Gerente
    gerente, created = User.objects.get_or_create(
        username='gerente_donpepe',
        defaults={
            'email': 'gerente@donpepe.cl',
            'rut': '23456789-6',
            'role': 'gerente',
            'company': company,
            'first_name': 'María',
            'last_name': 'López',
            'is_active': True
        }
    )
    if created:
        gerente.set_password('Gerente123!')
        gerente.save()
    print(f"   ✓ Gerente: {gerente.username} / Gerente123!")
    
    # Vendedor
    vendedor, created = User.objects.get_or_create(
        username='vendedor1',
        defaults={
            'email': 'vendedor1@donpepe.cl',
            'rut': '34567890-7',
            'role': 'vendedor',
            'company': company,
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'is_active': True
        }
    )
    if created:
        vendedor.set_password('Vendedor123!')
        vendedor.save()
    print(f"   ✓ Vendedor: {vendedor.username} / Vendedor123!")
    
    # 4. Crear Sucursales
    print("\n🏪 Creando sucursales...")
    sucursal1, created = Branch.objects.get_or_create(
        company=company,
        name='Sucursal Centro',
        defaults={
            'address': 'Av. Alemania 685, Temuco',
            'phone': '+56912345678',
            'email': 'centro@donpepe.cl',
            'is_active': True
        }
    )
    print(f"   ✓ {sucursal1.name}")
    
    sucursal2, created = Branch.objects.get_or_create(
        company=company,
        name='Sucursal Mall',
        defaults={
            'address': 'Mall Portal Temuco, Local 105',
            'phone': '+56987654321',
            'email': 'mall@donpepe.cl',
            'is_active': True
        }
    )
    print(f"   ✓ {sucursal2.name}")
    
    # 5. Crear Proveedores
    print("\n🚚 Creando proveedores...")
    proveedor1, created = Supplier.objects.get_or_create(
        company=company,
        rut='96123456-8',
        defaults={
            'name': 'Distribuidora Sur Ltda',
            'contact_name': 'Carlos Muñoz',
            'contact_phone': '+56945678901',
            'contact_email': 'ventas@distrisur.cl',
            'address': 'Parque Industrial, Temuco',
            'is_active': True
        }
    )
    print(f"   ✓ {proveedor1.name}")
    
    proveedor2, created = Supplier.objects.get_or_create(
        company=company,
        rut='97234567-9',
        defaults={
            'name': 'Alimentos Frescos SA',
            'contact_name': 'Ana Torres',
            'contact_phone': '+56956789012',
            'contact_email': 'contacto@alifrescos.cl',
            'address': 'Ruta 5 Sur Km 678',
            'is_active': True
        }
    )
    print(f"   ✓ {proveedor2.name}")
    
    # 6. Crear Categorías
    print("\n📂 Creando categorías...")
    categorias = []
    for cat_name in ['Abarrotes', 'Bebidas', 'Lácteos', 'Panadería', 'Carnes', 'Limpieza']:
        cat, created = Category.objects.get_or_create(
            company=company,
            name=cat_name,
            defaults={'description': f'Productos de {cat_name}'}
        )
        categorias.append(cat)
        print(f"   ✓ {cat.name}")
    
    # 7. Crear Productos
    print("\n🛒 Creando productos...")
    productos_data = [
        {'sku': 'ARR-001', 'name': 'Arroz Grado 1 1kg', 'category': 0, 'price': 1200, 'cost': 800},
        {'sku': 'FID-001', 'name': 'Fideos Carozzi 400g', 'category': 0, 'price': 800, 'cost': 550},
        {'sku': 'ACE-001', 'name': 'Aceite Vegetal 1L', 'category': 0, 'price': 2500, 'cost': 1800},
        {'sku': 'BEB-001', 'name': 'Coca Cola 1.5L', 'category': 1, 'price': 1500, 'cost': 1000},
        {'sku': 'BEB-002', 'name': 'Agua Mineral 2L', 'category': 1, 'price': 800, 'cost': 500},
        {'sku': 'BEB-003', 'name': 'Jugo Natural 1L', 'category': 1, 'price': 1200, 'cost': 800},
        {'sku': 'LAC-001', 'name': 'Leche Entera 1L', 'category': 2, 'price': 900, 'cost': 650},
        {'sku': 'LAC-002', 'name': 'Yogurt Natural 1kg', 'category': 2, 'price': 1800, 'cost': 1200},
        {'sku': 'LAC-003', 'name': 'Queso Mantecoso 500g', 'category': 2, 'price': 3500, 'cost': 2500},
        {'sku': 'PAN-001', 'name': 'Pan Hallulla unidad', 'category': 3, 'price': 300, 'cost': 150},
        {'sku': 'PAN-002', 'name': 'Pan Integral molde', 'category': 3, 'price': 1500, 'cost': 1000},
        {'sku': 'CAR-001', 'name': 'Pollo Entero kg', 'category': 4, 'price': 3500, 'cost': 2800},
        {'sku': 'LIM-001', 'name': 'Detergente 1kg', 'category': 5, 'price': 2500, 'cost': 1600},
        {'sku': 'LIM-002', 'name': 'Cloro 1L', 'category': 5, 'price': 1200, 'cost': 700},
        {'sku': 'LIM-003', 'name': 'Shampoo 400ml', 'category': 5, 'price': 2800, 'cost': 1900},
    ]
    
    productos = []
    for i, prod_data in enumerate(productos_data):
        prod, created = Product.objects.get_or_create(
            company=company,
            sku=prod_data['sku'],
            defaults={
                'name': prod_data['name'],
                'category': categorias[prod_data['category']],
                'supplier': proveedor1 if i % 2 == 0 else proveedor2,
                'price': Decimal(str(prod_data['price'])),
                'cost': Decimal(str(prod_data['cost'])),
                'is_active': True
            }
        )
        productos.append(prod)
        print(f"   ✓ {prod.sku} - {prod.name}")
    
    # 8. Crear Inventario
    print("\n📊 Creando inventario...")
    for sucursal in [sucursal1, sucursal2]:
        for producto in productos:
            stock = 50 if sucursal == sucursal1 else 30
            inv, created = Inventory.objects.get_or_create(
                branch=sucursal,
                product=producto,
                defaults={
                    'stock': stock,
                    'reorder_point': 10
                }
            )
        print(f"   ✓ Inventario creado para {sucursal.name}")
    
    # 9. Crear una venta de ejemplo
    print("\n💰 Creando venta de ejemplo...")
    sale = Sale.objects.create(
        branch=sucursal1,
        user=vendedor,
        total=Decimal('5500'),
        payment_method='efectivo',
        notes='Venta de prueba'
    )
    
    SaleItem.objects.create(
        sale=sale,
        product=productos[0],  # Arroz
        quantity=2,
        price=productos[0].price,
        subtotal=productos[0].price * 2
    )
    
    SaleItem.objects.create(
        sale=sale,
        product=productos[3],  # Coca Cola
        quantity=2,
        price=productos[3].price,
        subtotal=productos[3].price * 2
    )
    
    print(f"   ✓ Venta #{sale.id} creada por {vendedor.username}")
    
    # Resumen
    print("\n" + "="*50)
    print("✅ DATOS CREADOS EXITOSAMENTE")
    print("="*50)
    print(f"\n🏢 Empresa: {company.name}")
    print(f"👥 Usuarios creados:")
    print(f"   - admin / TemucoAdmin2025! (super_admin)")
    print(f"   - admin_donpepe / Admin123! (admin_cliente)")
    print(f"   - gerente_donpepe / Gerente123! (gerente)")
    print(f"   - vendedor1 / Vendedor123! (vendedor)")
    print(f"\n🏪 Sucursales: {Branch.objects.filter(company=company).count()}")
    print(f"🚚 Proveedores: {Supplier.objects.filter(company=company).count()}")
    print(f"📂 Categorías: {Category.objects.filter(company=company).count()}")
    print(f"🛒 Productos: {Product.objects.filter(company=company).count()}")
    print(f"📊 Registros de inventario: {Inventory.objects.filter(branch__company=company).count()}")
    print(f"💰 Ventas: {Sale.objects.filter(branch__company=company).count()}")
    print("\n🎉 ¡Listo para usar!\n")

if __name__ == '__main__':
    create_data()
