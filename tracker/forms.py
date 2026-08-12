from django import forms
from .models import Transaction, BudgetLimit, RecurringTransaction
from .models import ExpenseGroup, SharedExpense
from .models import TransactionTemplate
from .models import SavingsProfile
from .models import CreditCard
from .models import SavingsGoal


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



class ExpenseGroupForm(forms.ModelForm):
    class Meta:
        model = ExpenseGroup
        fields = ['name', 'members']
        widgets = {
            'members': forms.CheckboxSelectMultiple(), # Üyeleri çoklu seçim kutusu olarak gösterir
        }

class SharedExpenseForm(forms.ModelForm):
    class Meta:
        model = SharedExpense
        fields = ['group', 'title', 'amount', 'currency', 'paid_by', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'date', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Netflix'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tutar'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TransactionTemplateForm(forms.ModelForm):
    class Meta:
        model = TransactionTemplate
        fields = ['title', 'amount', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Sabah Kahvesi'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tutar (TL)'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kategori'}),
        }




class SavingsProfileForm(forms.ModelForm):
    class Meta:
        model = SavingsProfile
        fields = ['investment_rate', 'emergency_rate', 'other_rate']
        widgets = {
            'investment_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'emergency_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'investment_rate': 'Yatırım Oranı',
            'emergency_rate': 'Acil Durum Oranı',
            'other_rate': 'Diğer Oran',
        }

class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ['card_name', 'limit', 'current_debt', 'due_date', 'minimum_payment']
        widgets = {
            'card_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: İş Bankası Maximum'}),
            'limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000'}),
            'current_debt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '12500'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'minimum_payment': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '3750'}),
        }

class SavingsGoalForm(forms.ModelForm):
    class Meta:
        model = SavingsGoal
        fields = ['title', 'target_amount', 'current_amount']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Laptop Almak'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '40000'}),
            'current_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '17500'}),
        }