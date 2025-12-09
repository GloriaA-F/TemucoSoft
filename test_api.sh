#!/bin/bash

echo "================================================"
echo "   PRUEBA DE API - TemucoSoft"
echo "================================================"
echo ""

BASE_URL="http://100.31.181.235"

# 1. Obtener token
echo "1️⃣  Obteniendo token JWT..."
TOKEN_RESPONSE=$(curl -s -X POST $BASE_URL/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"vendedor1","password":"Vendedor123!"}')

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Error: No se pudo obtener el token"
    exit 1
fi

echo "✅ Token obtenido: ${TOKEN:0:50}..."
echo ""

# 2. Info del usuario
echo "2️⃣  Información del usuario..."
curl -s $BASE_URL/api/users/me/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# 3. Listar productos
echo "3️⃣  Listando productos (primeros 3)..."
curl -s "$BASE_URL/api/products/?page_size=3" | python3 -m json.tool
echo ""

# 4. Listar sucursales
echo "4️⃣  Listando sucursales..."
curl -s $BASE_URL/api/branches/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# 5. Inventario
echo "5️⃣  Inventario (primeros 3 items)..."
curl -s "$BASE_URL/api/inventory/?page_size=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# 6. Reporte de stock
echo "6️⃣  Reporte de stock (primeros 5 items)..."
curl -s "$BASE_URL/api/reports/stock/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -80
echo ""

echo "================================================"
echo "   ✅ PRUEBAS COMPLETADAS"
echo "================================================"
