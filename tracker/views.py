from datetime import date
from decimal import Decimal
import openpyxl
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponse

from .models import Transaction, BudgetLimit
from .forms import TransactionForm, BudgetLimitForm



def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})



def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'tracker/logout.html')



@login_required(login_url='login')
def home(request):
    user_transactions = Transaction.objects.filter(user=request.user)
    user_limits = BudgetLimit.objects.filter(user=request.user)
    

    current_month = date.today().month
    current_year = date.today().year
    
    for limit_obj in user_limits:
        
        category_expenses = user_transactions.filter(
            category=limit_obj.category,
            transaction_type='EXPENSE',
            date__year=current_year,
            date__month=current_month
        )
        
        total_spent = sum([t.amount for t in category_expenses], Decimal('0.00'))
        limit_val = limit_obj.monthly_limit
        
        if limit_val > 0:
            percentage = (total_spent / limit_val) * Decimal('100')
            
            if percentage >= 100:
                messages.error(request, f"🚨 DİKKAT! '{limit_obj.category.name}' kategorisindeki aylık bütçe limitinizi aştınız! Harcama: {total_spent} / Limit: {limit_val} TRY")
            elif percentage >= 80:
                messages.warning(request, f"⚠️ UYARI: '{limit_obj.category.name}' kategorisindeki bütçenizin %80'ine ulaştınız. Harcama: {total_spent} / Limit: {limit_val} TRY")

    context = {
        'transactions': user_transactions,
        'user_limits': user_limits
    }
    return render(request, 'tracker/home.html', context)



@login_required(login_url='login')
def transaction_add(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            form.save_m2m()
            messages.success(request, "İşlem başarıyla eklendi!")
            return redirect('home')
    else:
        form = TransactionForm()
    
    return render(request, 'tracker/transaction_form.html', {'form': form, 'action': 'Ekle'})



@login_required(login_url='login')
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, "İşlem başarıyla güncellendi!")
            return redirect('home')
    else:
        form = TransactionForm(instance=transaction)
        
    return render(request, 'tracker/transaction_form.html', {'form': form, 'action': 'Düzenle'})



@login_required(login_url='login')
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.error(request, "İşlem sistemden silindi.")
        return redirect('home')
        
    return render(request, 'tracker/transaction_confirm_delete.html', {'transaction': transaction})



@login_required(login_url='login')
def export_transactions_excel(request):
    transactions = Transaction.objects.filter(user=request.user)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Finansal Islemler"
    
    ws.append(["Baslik", "Miktar", "Tur", "Tarih", "Doviz", "Aciklama"])
    
    for t in transactions:
        ws.append([
            t.title,
            float(t.amount),
            t.get_transaction_type_display(),
            str(t.date),
            t.currency,
            t.description or ""
        ])
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=finans_raporu.xlsx'
    wb.save(response)
    
    return response



@login_required(login_url='login')
def import_transactions_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                title, amount, trans_type_display, date_val, currency, description = row[:6]
                
                if not title or not amount:
                    continue
                
                trans_type = 'INCOME' if trans_type_display == 'Gelir' else 'EXPENSE'
                
                Transaction.objects.create(
                    user=request.user,
                    title=title,
                    amount=amount,
                    transaction_type=trans_type,
                    date=date_val if date_val else date.today(),
                    currency=currency if currency else 'TRY',
                    description=description
                )
                
            messages.success(request, "Excel dosyasındaki veriler başarıyla içe aktarıldı!")
        except Exception as e:
            messages.error(request, f"Dosya okunurken bir hata oluştu: {e}")
            
        return redirect('home')
        
    return render(request, 'tracker/import_excel.html')



@login_required(login_url='login')
def set_budget_limit(request):
    if request.method == 'POST':
        form = BudgetLimitForm(request.POST)
        if form.is_valid():
            limit_obj = form.save(commit=False)
            limit_obj.user = request.user
            
            existing = BudgetLimit.objects.filter(user=request.user, category=limit_obj.category).first()
            if existing:
                existing.monthly_limit = limit_obj.monthly_limit
                existing.save()
            else:
                limit_obj.save()
                
            messages.success(request, "Bütçe limiti başarıyla kaydedildi!")
            return redirect('home')
    else:
        form = BudgetLimitForm()
        
    return render(request, 'tracker/set_limit.html', {'form': form})