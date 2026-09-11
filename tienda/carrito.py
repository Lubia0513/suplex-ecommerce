class Carrito:
    def __init__(self, request):
        self.session = request.session
        carrito = self.session.get('session_key')
        if 'session_key' not in request.session:
            carrito = self.session['session_key'] = {}
        self.carrito = carrito

    def agregar(self, producto):
        producto_id = str(producto.id)
        if producto_id in self.carrito:
            self.carrito[producto_id]['cantidad'] += 1
        else:
            self.carrito[producto_id] = {
                'producto_id': producto.id,
                'precio': str(producto.precio),
                'cantidad': 1,
                'nombre': producto.nombre,
                # Guardamos la imagen si existe
                'imagen_url': producto.imagen.url if producto.imagen else '' 
            }
        self.guardar()

    # --- NUEVA FUNCIÓN PARA RESTAR ---
    def restar(self, producto):
        producto_id = str(producto.id)
        if producto_id in self.carrito:
            self.carrito[producto_id]['cantidad'] -= 1
            # Si llega a 0, llamamos a la función de eliminar
            if self.carrito[producto_id]['cantidad'] <= 0:
                self.eliminar(producto)
            else:
                self.guardar()

    def eliminar(self, producto):
        producto_id = str(producto.id)
        if producto_id in self.carrito:
            del self.carrito[producto_id]
            self.guardar()

    def guardar(self):
        self.session.modified = True

    def limpiar(self):
        self.session['session_key'] = {}
        self.guardar()

    def obtener_total_items(self):
        return sum(item['cantidad'] for item in self.carrito.values())