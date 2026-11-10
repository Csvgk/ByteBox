from .cart import Cart
from .models import Category


def cart(request):
    """Дані, потрібні на кожній сторінці: категорії для меню і кількість товарів у кошику."""
    return {
        'nav_categories': Category.objects.all(),
        'cart_count': len(Cart(request)),
    }
