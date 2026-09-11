from django.shortcuts import render, redirect,get_object_or_404
from .models import Producto
from .carrito import Carrito
from .forms import PedidoForm
from django.contrib import messages
from .models import Producto, Pedido, DetallePedido, Categoria
import urllib.parse
from django.db.models import Sum, F, Count
from django.contrib.auth.decorators import user_passes_test, login_required
import datetime
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm


def catalogo(request):
    # Traemos todos los productos y todas las categorías (Proteínas, Creatinas, etc.)
    productos = Producto.objects.filter(disponible=True)
    categorias = Categoria.objects.all()
    
    # Leemos si el usuario hizo una búsqueda o presionó un filtro
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    
    # Aplicamos los filtros si existen
    if query:
        # Busca palabras que coincidan en el nombre del suplemento
        productos = productos.filter(nombre__icontains=query)
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
        
    # Extraemos los productos marcados para las secciones especiales (máximo 4 para no saturar)
    populares = Producto.objects.filter(disponible=True, es_popular=True)[:4]
    promociones = Producto.objects.filter(disponible=True, en_promocion=True)[:4]
    # Obtenemos los datos del carrito para el panel lateral
    carrito = Carrito(request)
    items_carrito = carrito.carrito.values()
    total_carrito = sum(float(item['precio']) * item['cantidad'] for item in items_carrito)
    
    contexto = {
        'productos': productos,
        'categorias': categorias,
        'populares': populares,
        'promociones': promociones,
        'query': query,
        'categoria_actual': int(categoria_id) if categoria_id else None,
        'items_carrito': items_carrito,  # NUEVO
        'total_carrito': total_carrito,  # NUEVO
    }
    return render(request, 'tienda/catalogo.html', contexto)
def agregar_al_carrito(request, producto_id):
    # Inicializamos el carrito de la sesión actual
    carrito = Carrito(request)
    # Buscamos el producto en la base de datos (si no existe, da un error 404 seguro)
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Usamos nuestro método para agregarlo
    carrito.agregar(producto)
    
    # Por ahora, simplemente recargamos la página del catálogo
    return redirect('catalogo')

def ver_carrito(request):
    # Recuperamos el carrito actual
    carrito = Carrito(request)
    
    # Extraemos los items del diccionario para poder usarlos fácilmente en el HTML
    items_carrito = carrito.carrito.values()
    
    # Calculamos el gran total sumando (precio * cantidad) de cada producto
    total_pagar = sum(float(item['precio']) * item['cantidad'] for item in items_carrito)
    
    contexto = {
        'items': items_carrito,
        'total_pagar': total_pagar
    }
    
    return render(request, 'tienda/carrito.html', contexto)

def checkout(request):
    carrito = Carrito(request)
    
    if carrito.obtener_total_items() == 0:
        return redirect('catalogo')

    if request.method == 'POST':
        # El usuario presionó el botón, recibimos los datos del formulario
        form = PedidoForm(request.POST)
        
        if form.is_valid():
            # 1. Validación de Inventario (Pre-compra)
            hay_error_stock = False
            for producto_id, item in carrito.carrito.items():
                producto_db = Producto.objects.get(id=producto_id)
                # Si alguien pide más de lo que tienes físicamente
                if producto_db.stock < item['cantidad']:
                    messages.error(request, f"Stock insuficiente para {producto_db.nombre}. Solo quedan {producto_db.stock} unidades.")
                    hay_error_stock = True
                    break
            
            # 2. Si todo está bien, procesamos la orden
            if not hay_error_stock:
                # Guardamos la dirección pero aún no lo enviamos a la BD (commit=False)
                pedido = form.save(commit=False)
                # Aquí, si usaras inicio de sesión, podrías asignar: pedido.cliente = request.user
                pedido.save() # Ahora sí creamos el ID del pedido

                # 3. Crear los detalles del pedido y restar inventario
                for producto_id, item in carrito.carrito.items():
                    producto_db = Producto.objects.get(id=producto_id)
                    
                    # Restamos la cantidad comprada de tu inventario real
                    producto_db.stock -= item['cantidad']
                    
                    # Si el producto se agota con esta compra, lo ocultamos del catálogo automáticamente
                    if producto_db.stock == 0:
                        producto_db.disponible = False
                        
                    producto_db.save()

                    # Guardamos el registro de qué se compró exactamente
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto_db,
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio']
                    )

                # 4. Vaciamos el carrito y redirigimos a la pantalla de éxito
                carrito.limpiar()
                return redirect('pedido_exitoso', pedido_id=pedido.id)

    else:
        # Si es una petición GET normal, solo mostramos el formulario vacío
        form = PedidoForm()

    items_carrito = carrito.carrito.values()
    total_pagar = sum(float(item['precio']) * item['cantidad'] for item in items_carrito)

    contexto = {
        'form': form,
        'items': items_carrito,
        'total_pagar': total_pagar
    }
    return render(request, 'tienda/checkout.html', contexto)

# --- NUEVA VISTA PARA MOSTRAR EL ÉXITO DE LA COMPRA ---
def pedido_exitoso(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    total = sum(detalle.cantidad * detalle.precio_unitario for detalle in pedido.items.all())
    
    # 1. Armamos el mensaje para WhatsApp (Ahora con Nombre)
    mensaje = f"Hola, soy *{pedido.nombre_comprador}*. Acabo de realizar un pedido.\n\n"
    mensaje += "*Productos:*\n"
    for detalle in pedido.items.all():
        mensaje += f"- {detalle.cantidad}x {detalle.producto.nombre}\n"
    
    mensaje += f"\n*Total a pagar:* ${total}\n"
    mensaje += f"*Método de pago:* {pedido.metodo_pago}\n\n"
    mensaje += "*Dirección de entrega:*\n"
    mensaje += f"{pedido.calle} #{pedido.numero_exterior}, Col. {pedido.colonia}, CP {pedido.codigo_postal}\n"
    if pedido.referencias:
        mensaje += f"Ref: {pedido.referencias}\n"
    
    # 2. Link de Google Maps si el usuario marcó el mapa
    if pedido.latitud and pedido.longitud:
        mensaje += f"\n*Ubicación Exacta:* https://maps.google.com/?q={pedido.latitud},{pedido.longitud}\n"
    
    mensaje_codificado = urllib.parse.quote(mensaje)
    numero_whatsapp = "525611273777"  # <- Pon tu número aquí
    url_whatsapp = f"https://wa.me/{numero_whatsapp}?text={mensaje_codificado}"
    
    return render(request, 'tienda/pedido_exitoso.html', {
        'pedido': pedido, 
        'url_whatsapp': url_whatsapp,
        'total': total
    })

def eliminar_del_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Llamamos a nuestro nuevo método del carrito
    carrito.eliminar(producto)
    
    # Redirigimos de vuelta a la misma página del carrito para ver los cambios
    return redirect('ver_carrito')

def agregar_al_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.agregar(producto)
    return redirect('/?carrito=1') # Redirige al inicio indicando que el carrito se modificó

def restar_del_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.restar(producto)
    return redirect('/?carrito=1')

def eliminar_del_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.eliminar(producto)
    return redirect('/?carrito=1')

def es_admin(user):
    
    return user.is_staff


@login_required(login_url='login_admin') 
@user_passes_test(es_admin, login_url='login_admin')



def panel_administrador(request):
    hoy = timezone.now().date()
    # Rango de tiempo por defecto (Últimos 30 días)
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = hoy - datetime.timedelta(days=dias)
    
    # 1. Filtramos los pedidos pagados/confirmados en el rango de tiempo
    pedidos_rango = Pedido.objects.filter(fecha_creacion__date__gte=fecha_inicio)
    
    # 2. Métricas Generales
    total_pedidos = pedidos_rango.count()
    ingresos = sum(
        sum(item.cantidad * item.precio_unitario for item in pedido.items.all())
        for pedido in pedidos_rango
    )
    
    # Simulación de Ganancia (Asumiendo un margen de ganancia del 30% como ejemplo)
    # Lo ideal a futuro es que cada Producto tenga un campo 'costo_proveedor'
    ganancias = float(ingresos) * 0.30
    
    # 3. Productos más vendidos (Top 5)
    mas_vendidos = DetallePedido.objects.filter(pedido__fecha_creacion__date__gte=fecha_inicio) \
                    .values('producto__nombre') \
                    .annotate(total_vendido=Sum('cantidad')) \
                    .order_by('-total_vendido')[:5]
                    
    # 4. Alertas de Stock (Productos con 3 o menos unidades)
    alertas_stock = Producto.objects.filter(stock__lte=3).order_by('stock')
    
    # 5. Lista de todos los productos para la tabla de gestión
    todos_los_productos = Producto.objects.all().order_by('-disponible', 'stock')

    pedidos_recientes = Pedido.objects.all().order_by('-fecha_creacion')[:20]

    contexto = {
        'dias_filtro': dias,
        'total_pedidos': total_pedidos,
        'ingresos': ingresos,
        'ganancias': ganancias,
        'mas_vendidos': mas_vendidos,
        'alertas_stock': alertas_stock,
        'todos_los_productos': todos_los_productos,
        'pedidos_recientes': pedidos_recientes,
    }
    
    return render(request, 'tienda/dashboard.html', contexto)



def login_admin(request):
    # Si ya está logueado y es admin, lo mandamos directo al panel
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('panel_administrador')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                return redirect('panel_administrador')
            else:
                messages.error(request, "Acceso denegado. No tienes permisos de administrador.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()

    return render(request, 'tienda/login.html', {'form': form})

def logout_admin(request):
    logout(request)
    return redirect('catalogo')