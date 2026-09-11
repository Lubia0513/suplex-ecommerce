from django.contrib import admin
from .models import Categoria, Producto, Pedido, DetallePedido

# Registros básicos
admin.site.register(Categoria)
admin.site.register(Pedido)
admin.site.register(DetallePedido)

# Registro avanzado para Producto (para que se vea mejor en la tabla)
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'disponible')
    list_filter = ('disponible', 'categoria')
    search_fields = ('nombre',)