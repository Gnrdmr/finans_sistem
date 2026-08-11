
from django.urls import path
from .views import home, register_view, login_view, logout_view, subscription_calendar_view, transaction_add, transaction_edit, delete_transaction, export_transactions_excel, import_transactions_excel, recurring_add, create_expense_group, add_shared_expense, set_budget_limit, group_list, group_detail, settle_debts, monthly_analytics, subscription_calendar_view, templates_management_view, quick_add_transaction_view, savings_simulation_view

urlpatterns = [
    path('',home, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('add/', transaction_add, name='add_transaction'),
    path('edit/<int:pk>/', transaction_edit, name='transaction_edit'),
    path('delete/<int:pk>/', delete_transaction, name='delete_transaction'),
    path('export/excel/', export_transactions_excel, name='export_excel'),
    path('import/excel/', import_transactions_excel, name='import_excel'),
    path('set-limit/', set_budget_limit, name='set_budget_limit'),
    path('recurring/add/', recurring_add, name='recurring_add'),
    path('group/add/', create_expense_group, name='create_group'),
    path('shared-expense/add/', add_shared_expense, name='add_shared_expense'), 
    path('groups/', group_list, name='group_list'),
    path('groups/<int:group_id>/', group_detail, name='group_detail'),
    path('groups/<int:group_id>/settle/', settle_debts, name='settle_debts'),
    path('monthly-analytics/', monthly_analytics, name='monthly_analytics'),
    path('subscriptions/', subscription_calendar_view, name='subscription_calendar'),
    path('templates/', templates_management_view, name='manage_templates'),
    path('templates/quick-add/<int:template_id>/', quick_add_transaction_view, name='quick_add_transaction'),
    path('savings-simulation/', savings_simulation_view, name='savings_simulation'),
    ]