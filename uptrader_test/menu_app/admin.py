from django.contrib import admin
from .models import Menu, MenuItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('title', 'parent', 'raw_url', 'named_url', 'order', 'open_in_new_tab')
    ordering = ('parent_id', 'order')


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
    inlines = (MenuItemInline,)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'menu', 'parent', 'order', 'named_url', 'raw_url')
    list_filter = ('menu',)
    search_fields = ('title', 'named_url', 'raw_url')
