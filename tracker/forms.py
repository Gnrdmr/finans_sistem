from django import forms
from .models import Transaction, BudgetLimit, RecurringTransaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'transaction_type', 'category', 'currency', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class BudgetLimitForm(forms.ModelForm):
    class Meta:
        model = BudgetLimit
        fields = ['category', 'monthly_limit']

class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = ['title', 'amount', 'transaction_type', 'category', 'currency', 'interval', 'start_date', 'next_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'next_date': forms.DateInput(attrs={'type': 'date'}),
        }