from django import forms
from .models import Pedido

class PedidoForm(forms.ModelForm):
    # Mantenemos las coordenadas como opcionales para que no bloqueen la compra si el GPS falla
    latitud = forms.CharField(required=False, widget=forms.HiddenInput())
    longitud = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Pedido
        fields = ['nombre_comprador', 'calle', 'numero_exterior', 'colonia', 'codigo_postal', 'referencias', 'metodo_pago', 'latitud', 'longitud']
        
        widgets = {
            'nombre_comprador': forms.TextInput(attrs={'class': 'tu-clase'}),
            'calle': forms.TextInput(attrs={'class': 'tu-clase'}),
            'numero_exterior': forms.TextInput(attrs={'class': 'tu-clase'}),
            'colonia': forms.TextInput(attrs={'class': 'tu-clase'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'tu-clase'}),
            'referencias': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Fachada blanca, portón negro...'}),
        }