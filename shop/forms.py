from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'email', 'delivery', 'address', 'comment']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel', 'placeholder': '+380...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'delivery': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control',
                                              'placeholder': 'Місто, № відділення або адреса'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        # Для доставки адреса обов'язкова, для самовивозу — ні
        if cleaned.get('delivery') != Order.Delivery.PICKUP and not cleaned.get('address'):
            self.add_error('address', 'Вкажіть адресу або номер відділення.')
        return cleaned
