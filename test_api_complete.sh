#!/bin/bash

echo "================================================"
echo "   PRUEBA COMPLETA DE API - TemucoSoft"
echo "================================================"
echo ""

BASE_URL="http://100.31.181.235"

echo "🔐 PRUEBA 1: Autenticación con VENDEDOR"
echo "========================================"
TOKEN_VENDEDOR=$(curl -s -X POST $BASE_URL/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"vendedor1","password":"Vendedor123!"}' | grep -o '"access":"[^"]*' | cut -d'"' -f4)
echo "✅ Token vendedor obtenido"
echo ""

echo "🔐 PRUEBA 2: Autenticación con GERENTE"
echo "========================================"
TOKEN_GERENTE=$(curl -s -X POST $BASE_URL/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"gerente_donpepe","password":"Gerente123!"}' | grep -o '"access":"[^"]*' | cut -d'"' -f4)
echo "✅ Token gerente obtenido"
echo ""

echo "👤 PRUEBA 3: Info del usuario vendedor"
echo "========================================"
curl -s $BASE_URL/api/users/me/ \
  -H "Authorization: Bearer $TOKEN_VENDEDOR" | python3 -m json.tool
echo ""

echo "🛒 PRUEBA 4: Listar productos (público)"
echo "========================================"
curl -s "$BASE_URL/api/products/?page_size=3" | python3 -m json.tool
echo ""

echo "🏪 PRUEBA 5: Listar sucursales (vendedor)"
echo "========================================"
curl -s $BASE_URL/api/branches/ \
  -H "Authorization: Bearer $TOKEN_VENDEDOR" | python3 -m json.tool
echo ""

echo "📦 PRUEBA 6: Inventario (vendedor)"
echo "========================================"
curl -s "$BASE_URL/api/inventory/?page_size=3" \
  -H "Authorization: Bearer $TOKEN_VENDEDOR" | python3 -m json.tool
echo ""

echo "📊 PRUEBA 7: Reporte de stock (gerente)"
echo "========================================"
curl -s "$BASE_URL/api/reports/stock/" \
  -H "Authorization: Bearer $TOKEN_GERENTE" | python3 -m json.tool | head -100
echo ""

echo "💰 PRUEBA 8: Reporte de ventas (gerente)"
echo "========================================"
curl -s "$BASE_URL/api/reports/sales/" \
  -H "Authorization: Bearer $TOKEN_GERENTE" | python3 -m json.tool
echo ""

echo "🚚 PRUEBA 9: Listar proveedores (vendedor)"
echo "========================================"
curl -s $BASE_URL/api/suppliers/ \
  -H "Authorization: Bearer $TOKEN_VENDEDOR" | python3 -m json.tool
echo ""

echo "================================================"
echo "   ✅ TODAS LAS PRUEBAS COMPLETADAS"
echo "================================================"
