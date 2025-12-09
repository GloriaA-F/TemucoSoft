from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from core.models import User
from products.models import Product, Supplier, Category
from inventory.models import Branch, Inventory
from sales.models import Sale, SaleItem, Order, OrderItem
from shop.models import CartItem, Cart
from datetime import datetime, timedelta


# ==================== AUTH VIEWS ====================

def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Bienvenido {user.get_full_name() or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Tu cuenta está inactiva.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('login')


# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    """Dashboard principal"""
    context = {
        'total_products': Product.objects.filter(company=request.user.company).count() if request.user.company else 0,
        'total_branches': Branch.objects.filter(company=request.user.company).count() if request.user.company else 0,
        'total_suppliers': Supplier.objects.filter(company=request.user.company).count() if request.user.company else 0,
    }
    
    today = datetime.now().date()
    if request.user.company:
        context['sales_today'] = Sale.objects.filter(
            branch__company=request.user.company,
            created_at__date=today
        ).count()
        
        context['recent_sales'] = Sale.objects.filter(
            branch__company=request.user.company
        ).select_related('branch', 'user').order_by('-created_at')[:5]
    else:
        context['sales_today'] = 0
        context['recent_sales'] = []
    
    return render(request, 'dashboard/dashboard.html', context)


# ==================== PRODUCTS VIEWS ====================

@login_required
def product_list(request):
    """Lista de productos"""
    products = Product.objects.filter(company=request.user.company).select_related('category', 'supplier')
    
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) |
            Q(description__icontains=search)
        )
    
    category = request.GET.get('category')
    if category:
        products = products.filter(category_id=category)
    
    is_active = request.GET.get('is_active')
    if is_active == 'true':
        products = products.filter(is_active=True)
    elif is_active == 'false':
        products = products.filter(is_active=False)
    
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'categories': Category.objects.filter(company=request.user.company),
        'is_paginated': products.has_other_pages(),
        'page_obj': products,
    }
    
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, pk):
    """Detalle de un producto"""
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    inventory_items = Inventory.objects.filter(
        product=product,
        branch__company=request.user.company
    ).select_related('branch')
    
    context = {
        'product': product,
        'inventory_items': inventory_items,
    }
    
    return render(request, 'products/product_detail.html', context)


@login_required
def product_create(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            product = Product.objects.create(
                company=request.user.company,
                sku=request.POST.get('sku'),
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                category_id=request.POST.get('category') or None,
                supplier_id=request.POST.get('supplier') or None,
                price=request.POST.get('price'),
                cost=request.POST.get('cost'),
                is_active='is_active' in request.POST,
            )
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save()
            
            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Error al crear producto: {str(e)}')
    
    context = {
        'categories': Category.objects.filter(company=request.user.company),
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'form': {'is_active': {'value': True}},
    }
    
    return render(request, 'products/product_form.html', context)


@login_required
def product_edit(request, pk):
    """Editar producto"""
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        try:
            product.sku = request.POST.get('sku')
            product.name = request.POST.get('name')
            product.description = request.POST.get('description', '')
            product.category_id = request.POST.get('category') or None
            product.supplier_id = request.POST.get('supplier') or None
            product.price = request.POST.get('price')
            product.cost = request.POST.get('cost')
            product.is_active = 'is_active' in request.POST
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            
            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar producto: {str(e)}')
    
    context = {
        'form': {
            'instance': product,
            'sku': {'value': product.sku},
            'name': {'value': product.name},
            'description': {'value': product.description},
            'category': {'value': product.category_id},
            'supplier': {'value': product.supplier_id},
            'cost': {'value': product.cost},
            'price': {'value': product.price},
            'is_active': {'value': product.is_active},
        },
        'categories': Category.objects.filter(company=request.user.company),
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
    }
    
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, pk):
    """Eliminar producto"""
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Producto "{name}" eliminado exitosamente.')
        return redirect('product_list')
    
    return render(request, 'products/product_confirm_delete.html', {'product': product})


# ==================== SUPPLIERS VIEWS ====================

@login_required
def supplier_list(request):
    """Lista de proveedores"""
    suppliers = Supplier.objects.filter(company=request.user.company)
    
    search = request.GET.get('search')
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) | 
            Q(rut__icontains=search) |
            Q(contact_name__icontains=search)
        )
    
    paginator = Paginator(suppliers, 20)
    page = request.GET.get('page')
    suppliers = paginator.get_page(page)
    
    context = {
        'suppliers': suppliers,
        'is_paginated': suppliers.has_other_pages(),
        'page_obj': suppliers,
    }
    
    return render(request, 'suppliers/supplier_list.html', context)


@login_required
def supplier_create(request):
    """Crear proveedor"""
    if request.method == 'POST':
        try:
            supplier = Supplier.objects.create(
                company=request.user.company,
                name=request.POST.get('name'),
                rut=request.POST.get('rut'),
                contact_name=request.POST.get('contact_name'),
                contact_phone=request.POST.get('contact_phone'),
                contact_email=request.POST.get('contact_email'),
                address=request.POST.get('address', ''),
                is_active='is_active' in request.POST,
            )
            
            messages.success(request, f'Proveedor "{supplier.name}" creado exitosamente.')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Error al crear proveedor: {str(e)}')
    
    context = {
        'form': {'is_active': {'value': True}},
    }
    
    return render(request, 'suppliers/supplier_form.html', context)


@login_required
def supplier_edit(request, pk):
    """Editar proveedor"""
    supplier = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        try:
            supplier.name = request.POST.get('name')
            supplier.rut = request.POST.get('rut')
            supplier.contact_name = request.POST.get('contact_name')
            supplier.contact_phone = request.POST.get('contact_phone')
            supplier.contact_email = request.POST.get('contact_email')
            supplier.address = request.POST.get('address', '')
            supplier.is_active = 'is_active' in request.POST
            supplier.save()
            
            messages.success(request, f'Proveedor "{supplier.name}" actualizado exitosamente.')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar proveedor: {str(e)}')
    
    context = {
        'form': {
            'instance': supplier,
            'name': {'value': supplier.name},
            'rut': {'value': supplier.rut},
            'contact_name': {'value': supplier.contact_name},
            'contact_phone': {'value': supplier.contact_phone},
            'contact_email': {'value': supplier.contact_email},
            'address': {'value': supplier.address},
            'is_active': {'value': supplier.is_active},
        },
    }
    
    return render(request, 'suppliers/supplier_form.html', context)


@login_required
def supplier_delete(request, pk):
    """Eliminar proveedor"""
    supplier = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        name = supplier.name
        supplier.delete()
        messages.success(request, f'Proveedor "{name}" eliminado exitosamente.')
        return redirect('supplier_list')
    
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})
# ==================== BRANCHES VIEWS ====================

@login_required
def branch_list(request):
    """Lista de sucursales"""
    branches = Branch.objects.filter(company=request.user.company)
    
    search = request.GET.get('search')
    if search:
        branches = branches.filter(
            Q(name__icontains=search) | 
            Q(address__icontains=search)
        )
    
    context = {
        'branches': branches,
    }
    
    return render(request, 'branches/branch_list.html', context)


@login_required
def branch_create(request):
    """Crear sucursal"""
    if request.method == 'POST':
        try:
            branch = Branch.objects.create(
                company=request.user.company,
                name=request.POST.get('name'),
                address=request.POST.get('address'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email', ''),
                is_active='is_active' in request.POST,
            )
            
            messages.success(request, f'Sucursal "{branch.name}" creada exitosamente.')
            return redirect('branch_list')
        except Exception as e:
            messages.error(request, f'Error al crear sucursal: {str(e)}')
    
    context = {
        'form': {'is_active': {'value': True}},
    }
    
    return render(request, 'branches/branch_form.html', context)


@login_required
def branch_edit(request, pk):
    """Editar sucursal"""
    branch = get_object_or_404(Branch, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        try:
            branch.name = request.POST.get('name')
            branch.address = request.POST.get('address')
            branch.phone = request.POST.get('phone')
            branch.email = request.POST.get('email', '')
            branch.is_active = 'is_active' in request.POST
            branch.save()
            
            messages.success(request, f'Sucursal "{branch.name}" actualizada exitosamente.')
            return redirect('branch_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar sucursal: {str(e)}')
    
    context = {
        'form': {
            'instance': branch,
            'name': {'value': branch.name},
            'address': {'value': branch.address},
            'phone': {'value': branch.phone},
            'email': {'value': branch.email},
            'is_active': {'value': branch.is_active},
        },
    }
    
    return render(request, 'branches/branch_form.html', context)


@login_required
def branch_delete(request, pk):
    """Eliminar sucursal"""
    branch = get_object_or_404(Branch, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        name = branch.name
        branch.delete()
        messages.success(request, f'Sucursal "{name}" eliminada exitosamente.')
        return redirect('branch_list')
    
    return render(request, 'branches/branch_confirm_delete.html', {'branch': branch})


# ==================== INVENTORY VIEWS ====================

@login_required
def inventory_list(request):
    """Lista de inventario"""
    inventory_items = Inventory.objects.filter(
        branch__company=request.user.company
    ).select_related('product', 'branch')
    
    branch = request.GET.get('branch')
    if branch:
        inventory_items = inventory_items.filter(branch_id=branch)
    
    search = request.GET.get('search')
    if search:
        inventory_items = inventory_items.filter(
            Q(product__name__icontains=search) |
            Q(product__sku__icontains=search)
        )
    
    needs_reorder = request.GET.get('needs_reorder')
    if needs_reorder == 'true':
        inventory_items = [item for item in inventory_items if item.needs_reorder]
    
    paginator = Paginator(inventory_items, 20)
    page = request.GET.get('page')
    inventory_items = paginator.get_page(page)
    
    context = {
        'inventory_items': inventory_items,
        'branches': Branch.objects.filter(company=request.user.company, is_active=True),
        'is_paginated': inventory_items.has_other_pages(),
        'page_obj': inventory_items,
    }
    
    return render(request, 'inventory/inventory_list.html', context)


@login_required
def inventory_adjust(request):
    """Ajustar inventario"""
    if request.method == 'POST':
        try:
            branch_id = request.POST.get('branch')
            product_id = request.POST.get('product')
            quantity = int(request.POST.get('quantity'))
            reason = request.POST.get('reason')
            
            inventory, created = Inventory.objects.get_or_create(
                branch_id=branch_id,
                product_id=product_id,
                defaults={'stock': 0, 'reorder_point': 10}
            )
            
            inventory.adjust_stock(quantity, reason)
            
            messages.success(request, f'Inventario ajustado exitosamente. Nuevo stock: {inventory.stock}')
            return redirect('inventory_list')
        except Exception as e:
            messages.error(request, f'Error al ajustar inventario: {str(e)}')
    
    context = {
        'branches': Branch.objects.filter(company=request.user.company, is_active=True),
        'products': Product.objects.filter(company=request.user.company, is_active=True),
    }
    
    return render(request, 'inventory/inventory_adjust.html', context)


# ==================== SALES VIEWS ====================

@login_required
def sale_list(request):
    """Lista de ventas"""
    sales = Sale.objects.filter(
        branch__company=request.user.company
    ).select_related('branch', 'user').prefetch_related('items')
    
    branch = request.GET.get('branch')
    if branch:
        sales = sales.filter(branch_id=branch)
    
    date_from = request.GET.get('date_from')
    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    
    sales = sales.order_by('-created_at')
    
    paginator = Paginator(sales, 20)
    page = request.GET.get('page')
    sales = paginator.get_page(page)
    
    context = {
        'sales': sales,
        'branches': Branch.objects.filter(company=request.user.company, is_active=True),
        'is_paginated': sales.has_other_pages(),
        'page_obj': sales,
    }
    
    return render(request, 'sales/sale_list.html', context)


@login_required
def sale_create(request):
    """Crear nueva venta POS"""
    if request.method == 'POST':
        try:
            from django.db import transaction
            
            with transaction.atomic():
                branch_id = request.POST.get('branch')
                payment_method = request.POST.get('payment_method')
                notes = request.POST.get('notes', '')
                
                cart_items = request.session.get('pos_cart', [])
                
                if not cart_items:
                    messages.error(request, 'El carrito está vacío.')
                    return redirect('sale_create')
                
                total = sum(item['quantity'] * item['price'] for item in cart_items)
                
                sale = Sale.objects.create(
                    branch_id=branch_id,
                    user=request.user,
                    total=total,
                    payment_method=payment_method,
                    notes=notes
                )
                
                for item_data in cart_items:
                    SaleItem.objects.create(
                        sale=sale,
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                        subtotal=item_data['quantity'] * item_data['price']
                    )
                    
                    inventory = Inventory.objects.get(
                        branch_id=branch_id,
                        product_id=item_data['product_id']
                    )
                    inventory.adjust_stock(-item_data['quantity'], f"Venta POS #{sale.id}")
                
                request.session['pos_cart'] = []
                
                messages.success(request, f'Venta #{sale.id} registrada exitosamente. Total: ${total}')
                return redirect('sale_list')
                
        except Exception as e:
            messages.error(request, f'Error al crear venta: {str(e)}')
    
    cart_items = request.session.get('pos_cart', [])
    
    for item in cart_items:
        product = Product.objects.get(id=item['product_id'])
        item['product_name'] = product.name
        item['product_sku'] = product.sku
    
    context = {
        'branches': Branch.objects.filter(company=request.user.company, is_active=True),
        'products': Product.objects.filter(company=request.user.company, is_active=True),
        'cart_items': cart_items,
        'cart_total': sum(item['quantity'] * item['price'] for item in cart_items),
    }
    
    return render(request, 'sales/sale_create.html', context)


@login_required
def sale_add_item(request):
    """Agregar item al carrito POS"""
    if request.method == 'POST':
        try:
            product_id = int(request.POST.get('product'))
            quantity = int(request.POST.get('quantity'))
            
            product = Product.objects.get(id=product_id, company=request.user.company)
            
            cart = request.session.get('pos_cart', [])
            
            found = False
            for item in cart:
                if item['product_id'] == product_id:
                    item['quantity'] += quantity
                    found = True
                    break
            
            if not found:
                cart.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': float(product.price)
                })
            
            request.session['pos_cart'] = cart
            request.session.modified = True
            
            messages.success(request, f'Producto "{product.name}" agregado al carrito.')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('sale_create')


@login_required
def sale_remove_item(request, product_id):
    """Remover item del carrito POS"""
    cart = request.session.get('pos_cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]
    request.session['pos_cart'] = cart
    request.session.modified = True
    
    messages.info(request, 'Producto removido del carrito.')
    return redirect('sale_create')


@login_required
def sale_detail(request, pk):
    """Detalle de una venta"""
    sale = get_object_or_404(
        Sale.objects.select_related('branch', 'user').prefetch_related('items__product'),
        pk=pk,
        branch__company=request.user.company
    )
    
    context = {
        'sale': sale,
    }
    
    return render(request, 'sales/sale_detail.html', context)
# ==================== SHOP/CATALOG VIEWS ====================

def shop_catalog(request):
    """Catálogo público de productos (e-commerce)"""
    products = Product.objects.filter(is_active=True)
    
    if request.user.is_authenticated and request.user.company:
        products = products.filter(company=request.user.company)
    
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    category = request.GET.get('category')
    if category:
        products = products.filter(category_id=category)
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'categories': Category.objects.all()[:10],
        'is_paginated': products.has_other_pages(),
        'page_obj': products,
    }
    
    return render(request, 'shop/catalog.html', context)


def shop_product_detail(request, pk):
    """Detalle de producto en catálogo"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    
    return render(request, 'shop/product_detail.html', context)


# ==================== REPORTS VIEWS ====================

@login_required
def reports_sales(request):
    """Reporte de ventas"""
    from datetime import timedelta
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=30)
    
    if request.GET.get('date_from'):
        date_from = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d').date()
    
    if request.GET.get('date_to'):
        date_to = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d').date()
    
    sales = Sale.objects.filter(
        branch__company=request.user.company,
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    total_sales = sales.count()
    total_revenue = sales.aggregate(Sum('total'))['total__sum'] or 0
    
    by_branch = sales.values('branch__name').annotate(
        count=Count('id'),
        revenue=Sum('total')
    ).order_by('-revenue')
    
    by_payment = sales.values('payment_method').annotate(
        count=Count('id'),
        revenue=Sum('total')
    ).order_by('-revenue')
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'by_branch': by_branch,
        'by_payment': by_payment,
        'branches': Branch.objects.filter(company=request.user.company),
    }
    
    return render(request, 'reports/sales.html', context)


@login_required
def reports_stock(request):
    """Reporte de stock"""
    inventory_items = Inventory.objects.filter(
        branch__company=request.user.company
    ).select_related('product', 'branch')
    
    branch = request.GET.get('branch')
    if branch:
        inventory_items = inventory_items.filter(branch_id=branch)
    
    low_stock = request.GET.get('low_stock')
    if low_stock == 'true':
        inventory_items = [item for item in inventory_items if item.needs_reorder]
    
    context = {
        'inventory_items': inventory_items,
        'branches': Branch.objects.filter(company=request.user.company),
        'total_items': len(inventory_items),
        'low_stock_count': sum(1 for item in inventory_items if item.needs_reorder),
    }
    
    return render(request, 'reports/stock.html', context)
