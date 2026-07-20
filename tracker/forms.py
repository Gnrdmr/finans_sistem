from django import forms
from .models import BudgetLimit, Transaction


class TransactionForm(forms.ModelForm):

  class Meta:
    model = Transaction
    fields = ['title', 'amount', 'transaction_type', 'date']
    widgets = {
        'date': forms.DateInput(attrs={'type': 'date'}),
    }  


class BudgetLimitForm(forms.ModelForm):
  class Meta:
    model = BudgetLimit
    fields = ['category', 'monthly_limit']