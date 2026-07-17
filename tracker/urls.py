from django.urls import path
from .views import home, register_view, login_view, logout_view, transaction_add, transaction_edit, transaction_delete, export_transactions_excel, import_transactions_excel

urlpatterns = [
    path('',home, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('add/', transaction_add, name='transaction_add'),
    path('edit/<int:pk>/', transaction_edit, name='transaction_edit'),
    path('delete/<int:pk>/', transaction_delete, name='transaction_delete'),
    path('export/excel/', export_transactions_excel, name='export_excel'),
    path('import/excel/', import_transactions_excel, name='import_excel'),

]