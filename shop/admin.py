from django.contrib import admin

from .models import Brand, Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'price', 'stock', 'is_active']
    list_filter = ['category', 'brand', 'is_active']
    list_editable = ['price', 'stock', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ['name']}
    fieldsets = [
        ('Основне', {'fields': ['category', 'brand', 'name', 'slug', 'description', 'image']}),
        ('Ціна і склад', {'fields': ['price', 'old_price', 'stock', 'is_active']}),
        ('Сумісність', {'fields': ['socket', 'memory_type', 'form_factor', 'power_draw', 'psu_power']}),
        ('Інші характеристики', {'fields': ['specs']}),
    ]
