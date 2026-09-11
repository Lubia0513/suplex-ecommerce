from django.db import models
from django.contrib.auth.models import User

# 1. Tabla de Categorías (Para organizar el catálogo)
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

# 2. Tabla de Productos
class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    # Ejemplos: "Creatina Monohidratada 500g", "Pre-entreno Get Raw Nutrition"
    nombre = models.CharField(max_length=200) 
    descripcion = models.TextField(help_text="Ingredientes, modo de uso y beneficios.")
    # Usamos DecimalField para manejar precios con exactitud y evitar errores de redondeo
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.IntegerField(default=0, help_text="Unidades físicas disponibles")
    disponible = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
   
    es_popular = models.BooleanField(default=False, help_text="Mostrar en sección de Populares")
    en_promocion = models.BooleanField(default=False, help_text="Mostrar en sección de Promociones")
    descuento_porcentaje = models.PositiveIntegerField(default=0, help_text="Ejemplo: 10 para 10% de descuento")
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock}"

# 3. Tabla de Pedidos (La cabecera de la orden)
class Pedido(models.Model):
    ESTADOS = (
        ('Pendiente', 'Pendiente de confirmación'),
        ('En Camino', 'En ruta de entrega'),
        ('Entregado', 'Entregado al cliente'),
    )
    # Agregamos las opciones de pago
    METODOS_PAGO = (
        ('Efectivo', 'Efectivo contra entrega'),
        ('Transferencia', 'Transferencia Bancaria'),
    )
    
    cliente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')

    # --- NUEVOS CAMPOS ---
    nombre_comprador = models.CharField(max_length=150, default='')
    latitud = models.CharField(max_length=50, default='', blank=True, null=True)
    longitud = models.CharField(max_length=50, default='', blank=True, null=True)
    
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='Efectivo')
    
    # Dirección dividida (usamos default='' para no tener errores con pedidos antiguos)
    calle = models.CharField(max_length=150, default='')
    numero_exterior = models.CharField(max_length=20, default='')
    colonia = models.CharField(max_length=100, default='')
    codigo_postal = models.CharField(max_length=10, default='')
    referencias = models.TextField(help_text="Fachada, color de casa, etc.", blank=True, null=True)
    
    def __str__(self):
        return f"Pedido #{self.id} - Estado: {self.estado}"

# 4. Tabla de Detalle de Pedidos (Los productos específicos dentro de una orden)
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    # Guardamos el precio al momento de la compra, por si el precio del producto cambia después
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"