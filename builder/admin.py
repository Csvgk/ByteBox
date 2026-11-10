from django.contrib import admin
from django.utils.html import format_html_join

from .models import Build


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ['name', 'purpose', 'is_prebuilt', 'user', 'total_price_display', 'created_at']
    list_filter = ['is_prebuilt', 'purpose']
    search_fields = ['name', 'user__username']
    prepopulated_fields = {'slug': ['name']}
    readonly_fields = ['compatibility_report']
    fieldsets = [
        ('Основне', {'fields': ['name', 'slug', 'description', 'purpose', 'image', 'is_prebuilt', 'user']}),
        ('Комплектуючі', {'fields': ['cpu', 'motherboard', 'ram', 'gpu', 'storage', 'psu', 'case']}),
        ('Перевірка сумісності', {'fields': ['compatibility_report']}),
    ]

    @admin.display(description='Ціна')
    def total_price_display(self, obj):
        return f'{obj.total_price:.0f} грн'

    @admin.display(description='Результат перевірки')
    def compatibility_report(self, obj):
        if not obj.pk:
            return 'Збережіть збірку, щоб побачити перевірку.'
        icons = {'error': '❌', 'warning': '⚠️', 'ok': '✅'}
        return format_html_join('', '<div>{} {}</div>', ((icons[level], text) for level, text in obj.compatibility()))
