from django.contrib.auth import views
from django.urls import path
from .views import home, register_view, login_view, logout_view, transaction_add, transaction_edit, transaction_delete, export_transactions_excel, import_transactions_excel, recurring_add, create_expense_group, add_shared_expense, set_budget_limit, group_list, group_detail, settle_debts

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
    path('set-limit/', set_budget_limit, name='set_limit'),
    path('recurring/add/', recurring_add, name='recurring_add'),
    path('group/add/', create_expense_group, name='create_group'),
    path('shared-expense/add/', add_shared_expense, name='add_shared_expense'), 
    path('groups/', group_list, name='group_list'),
    path('groups/<int:group_id>/', group_detail, name='group_detail'),
    path('groups/<int:group_id>/settle/', settle_debts, name='settle_debts'),
    ]