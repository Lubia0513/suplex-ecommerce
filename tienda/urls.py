from django.urls import path
from . import views

urlpatterns = [
    # La ruta vacía '' significa que será la página principal de tu sitio
    path('', views.catalogo, name='catalogo'), 
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('checkout/', views.checkout, name='checkout'),
    path('exito/<int:pedido_id>/', views.pedido_exitoso, name='pedido_exitoso'),
    path('eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('restar/<int:producto_id>/', views.restar_del_carrito, name='restar_del_carrito'),
    path('panel', views.panel_administrador, name='panel_administrador'),
    path('panel/login/', views.login_admin, name='login_admin'),
    path('panel/logout/', views.logout_admin, name='logout_admin'),
]   