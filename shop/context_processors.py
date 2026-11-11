from .cart import Cart
from .models import Category


def cart(request):
    return {
        'nav_categories': Category.objects.all(),
        'cart_count': len(Cart(request)),
    }
