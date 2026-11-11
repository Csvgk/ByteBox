from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from blog.models import Post

from .cart import Cart
from .forms import OrderForm
from .models import Brand, Category, Order, OrderItem, Product

SORT_OPTIONS = {
    'new': ('-created_at', 'Спочатку нові'),
    'cheap': ('price', 'Спочатку дешеві'),
    'expensive': ('-price', 'Спочатку дорогі'),
    'name': ('name', 'За назвою'),
}


def home(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    context = {
        'categories': Category.objects.all(),
        'sale_products': products.filter(old_price__gt=F('price'))[:4],
        'new_products': products[:8],
        'latest_posts': Post.published.select_related('category')[:3],
    }
    return render(request, 'shop/home.html', context)


def catalog(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')

    category = None
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query) | Q(description__icontains=query))

    selected_brands = request.GET.getlist('brand')
    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)

    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price.isdigit():
        products = products.filter(price__gte=min_price)
    if max_price.isdigit():
        products = products.filter(price__lte=max_price)

    in_stock_only = request.GET.get('in_stock') == '1'
    if in_stock_only:
        products = products.filter(stock__gt=0)

    sort = request.GET.get('sort', 'new')
    if sort not in SORT_OPTIONS:
        sort = 'new'
    products = products.order_by(SORT_OPTIONS[sort][0])

    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    brands = Brand.objects.all()
    if category:
        brands = brands.filter(products__category=category).distinct()

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'brands': brands,
        'category': category,
        'query': query,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock_only': in_stock_only,
        'sort': sort,
        'sort_options': [(key, label) for key, (_, label) in SORT_OPTIONS.items()],
        'total': paginator.count,
    }
    return render(request, 'shop/catalog.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category', 'brand'), slug=slug, is_active=True)
    related = (Product.objects.filter(category=product.category, is_active=True)
               .exclude(id=product.id).select_related('category', 'brand')[:4])
    return render(request, 'shop/product_detail.html', {'product': product, 'related': related})


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart, 'lines': list(cart), 'total': cart.total_price()})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if not product.in_stock:
        messages.error(request, 'На жаль, цього товару немає в наявності.')
    else:
        quantity = int(request.POST.get('quantity', 1) or 1)
        Cart(request).add(product, quantity)
        messages.success(request, f'«{product.brand.name} {product.name}» додано в кошик.')
    next_url = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('shop:cart_detail')


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).set(product, int(request.POST.get('quantity', 1) or 0))
    return redirect('shop:cart_detail')


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    messages.info(request, 'Товар прибрано з кошика.')
    return redirect('shop:cart_detail')


@login_required
def checkout(request):
    cart = Cart(request)
    lines = list(cart)
    if not lines:
        messages.info(request, 'Кошик порожній.')
        return redirect('shop:catalog')

    initial = {'full_name': request.user.get_full_name(), 'email': request.user.email}
    form = OrderForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            products = {p.id: p for p in Product.objects.select_for_update().filter(
                id__in=[line['product'].id for line in lines])}

            for line in lines:
                product = products[line['product'].id]
                if product.stock < line['quantity']:
                    messages.error(request, f'«{product.name}»: на складі залишилось лише {product.stock} шт.')
                    return redirect('shop:cart_detail')

            order = form.save(commit=False)
            order.user = request.user
            order.total = cart.total_price()
            order.save()

            for line in lines:
                product = products[line['product'].id]
                OrderItem.objects.create(order=order, product=product, name=f'{product.brand.name} {product.name}',
                                         price=product.price, quantity=line['quantity'])
                product.stock -= line['quantity']
                product.save(update_fields=['stock'])

        cart.clear()
        messages.success(request, f'Дякуємо! Замовлення №{order.id} прийнято.')
        return redirect(order.get_absolute_url())

    return render(request, 'shop/checkout.html', {'form': form, 'lines': lines, 'total': cart.total_price()})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, user=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})
