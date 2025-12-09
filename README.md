# TemucoSoft - Sistema POS + E-commerce

Sistema modular de punto de venta y comercio electrónico con gestión de inventario, desarrollado con Django REST Framework.

## 🚀 Información del Servidor

- **IP Pública Web:** 100.31.181.235
- **IP Privada Web:** 172.31.66.81
- **IP Privada DB:** 172.31.74.124

## 📋 Características

- ✅ Sistema multi-tenant (múltiples empresas)
- ✅ Control de acceso por roles (super_admin, admin_cliente, gerente, vendedor)
- ✅ Gestión de productos, inventario y proveedores
- ✅ Punto de venta (POS)
- ✅ E-commerce con carrito de compras
- ✅ Reportes de ventas e inventario
- ✅ API RESTful con autenticación JWT
- ✅ Base de datos PostgreSQL
- ✅ Validación de RUT chileno
- ✅ Deploy en AWS EC2 con Nginx + Gunicorn

## 👥 Usuarios de Prueba

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | TemucoAdmin2025! | super_admin |
| admin_donpepe | Admin123! | admin_cliente |
| gerente_donpepe | Gerente123! | gerente |
| vendedor1 | Vendedor123! | vendedor |

## 🔗 Endpoints Principales

### Autenticación
```bash
# Obtener token JWT
POST http://100.31.181.235/api/token/
{
  "username": "vendedor1",
  "password": "Vendedor123!"
}

# Refrescar token
POST http://100.31.181.235/api/token/refresh/
{
  "refresh": "tu_refresh_token"
}
```

### Productos
```bash
GET http://100.31.181.235/api/products/
GET http://100.31.181.235/api/products/{id}/
POST http://100.31.181.235/api/products/
PUT http://100.31.181.235/api/products/{id}/
DELETE http://100.31.181.235/api/products/{id}/
```

### Inventario
```bash
GET http://100.31.181.235/api/inventory/
GET http://100.31.181.235/api/branches/
GET http://100.31.181.235/api/branches/{id}/inventory/
POST http://100.31.181.235/api/inventory/adjust/
```

### Ventas
```bash
GET http://100.31.181.235/api/sales/
POST http://100.31.181.235/api/sales/
GET http://100.31.181.235/api/orders/
POST http://100.31.181.235/api/orders/
```

### Reportes
```bash
GET http://100.31.181.235/api/reports/stock/
GET http://100.31.181.235/api/reports/sales/?date_from=2025-01-01&date_to=2025-12-31
```

### Proveedores
```bash
GET http://100.31.181.235/api/suppliers/
POST http://100.31.181.235/api/suppliers/
```

### Carrito de Compras
```bash
GET http://100.31.181.235/api/cart/
POST http://100.31.181.235/api/cart/add/
PATCH http://100.31.181.235/api/cart/{id}/update_quantity/
DELETE http://100.31.181.235/api/cart/{id}/remove/
POST http://100.31.181.235/api/cart/checkout/
```

## 🛠️ Instalación Local

### Requisitos
- Python 3.11+
- PostgreSQL 15+
- pip, virtualenv

### Pasos

1. Clonar repositorio y crear entorno virtual
```bash
cd ~/temucosoft
python3.11 -m venv venv
source venv/bin/activate
```

2. Instalar dependencias
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno (.env)
```
SECRET_KEY=tu-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=temucosoft_db
DB_USER=temucosoft_user
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

4. Aplicar migraciones
```bash
python manage.py migrate
```

5. Crear superusuario
```bash
python manage.py createsuperuser
```

6. Cargar datos de prueba
```bash
python populate_data.py
```

7. Ejecutar servidor de desarrollo
```bash
python manage.py runserver
```

## 📦 Deploy en Producción (AWS EC2)

### Instancia de Base de Datos
```bash
# Instalar PostgreSQL
sudo dnf install postgresql15-server postgresql15-contrib -y
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configurar PostgreSQL (pg_hba.conf y postgresql.conf)
# Ver documentación completa en el proyecto
```

### Instancia Web
```bash
# Instalar dependencias
sudo dnf install python3.11 python3.11-pip nginx git -y

# Configurar aplicación
cd ~/temucosoft
source venv/bin/activate
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Configurar Gunicorn
sudo nano /etc/systemd/system/gunicorn.service

# Iniciar servicios
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 📊 Estructura del Proyecto
```
temucosoft/
├── core/               # Usuarios, empresas, suscripciones
├── products/           # Productos, categorías, proveedores
├── inventory/          # Inventario, sucursales, compras
├── sales/              # Ventas POS y órdenes e-commerce
├── shop/               # Carrito de compras
├── temucosoft_project/ # Configuración Django
├── templates/          # Plantillas HTML
├── static/             # Archivos estáticos
├── media/              # Archivos subidos
└── logs/               # Logs de aplicación
```

## 🔐 Validaciones Implementadas

- ✅ Validación de RUT chileno (dígito verificador)
- ✅ Fechas de venta no pueden ser futuras
- ✅ Precios y costos >= 0
- ✅ Stock no puede ser negativo
- ✅ Cantidades >= 1 en ventas y órdenes

## 📝 Modelos Principales

- **User:** Usuarios con roles
- **Company:** Empresas cliente (multi-tenant)
- **Subscription:** Planes de suscripción
- **Product:** Productos
- **Supplier:** Proveedores
- **Branch:** Sucursales
- **Inventory:** Control de stock
- **Sale:** Ventas POS
- **Order:** Órdenes e-commerce
- **CartItem:** Items del carrito

## 🎯 Permisos por Rol

| Acción | super_admin | admin_cliente | gerente | vendedor |
|--------|------------|---------------|---------|----------|
| Gestionar empresas | ✅ | ❌ | ❌ | ❌ |
| Gestionar usuarios | ✅ | ✅ | ❌ | ❌ |
| Gestionar productos | ✅ | ✅ | ✅ | ❌ |
| Gestionar inventario | ✅ | ✅ | ✅ | ❌ |
| Ver reportes | ✅ | ✅ | ✅ | ❌ |
| Crear ventas | ✅ | ✅ | ✅ | ✅ |
| Ver productos | ✅ | ✅ | ✅ | ✅ |

## 📞 Soporte

Para más información, contactar al equipo de desarrollo de TemucoSoft.
GLORIA ANTIBIL Y NAYARETH MILLAHUAL

## 📄 Licencia

Proyecto académico - Evaluación Backend
