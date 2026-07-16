from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'transaction_type', 'date', 'currency', 'category', 'tags', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}), 
        }