from django.contrib import admin
from .models import Category, Tag, Transaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'transaction_type', 'currency', 'date', 'category')
    list_filter = ('transaction_type', 'currency', 'date', 'category')
    search_fields = ('title', 'description')
    date_hierarchy = 'date'
