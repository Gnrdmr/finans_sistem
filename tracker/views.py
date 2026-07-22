from datetime import date
from decimal import Decimal
import openpyxl
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from datetime import timedelta

from .models import Transaction, BudgetLimit, RecurringTransaction
from .forms import TransactionForm, BudgetLimitForm, RecurringTransactionForm
from .utils import convert_to_try, get_exchange_rates # Gün 8: Döviz çevirici ve kur servisimiz


# 1. Kayıt Olma Görünümü
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


# 2. Giriş Yapma Görünümü
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


# 3. Çıkış Yapma Görünümü
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'tracker/logout.html')


# 4. Ana Sayfa, Tekrarlayan İşlem Tetikleyicisi, Akıllı Bütçe Uyarıları, TRY Özet Hesabı ve Canlı Kurlar (Gün 8)
@login_required(login_url='login')
def home(request):
    user_transactions = Transaction.objects.filter(user=request.user)
    user_limits = BudgetLimit.objects.filter(user=request.user)
    
    # --- A. Her İşlemin TRY Karşılığını Hesaplama (Listeleme İçin) ---
    for t in user_transactions:
        t.try_amount = convert_to_try(t.amount, t.currency)
    
    # --- B. TEKRARLAYAN İŞLEMLER OTOMATİK KONTROLÜ (Gün 7) ---
    today = date.today()
    recurring_items = RecurringTransaction.objects.filter(user=request.user, is_active=True, next_date__lte=today)
    
    for item in recurring_items:
        Transaction.objects.create(
            user=item.user,
            title=f"{item.title} (Tekrarlayan)",
            amount=item.amount,
            transaction_type=item.transaction_type,
            date=item.next_date,
            currency=item.currency,
            category=item.category,
            description=f"Otomatik oluşturulan tekrarlayan işlem ({item.get_interval_display()})"
        )
        
        if item.interval == 'DAILY':
            item.next_date += timedelta(days=1)
        elif item.interval == 'WEEKLY':
            item.next_date += timedelta(weeks=1)
        elif item.interval == 'MONTHLY':
            item.next_date += relativedelta(months=1)
        elif item.interval == 'YEARLY':
            item.next_date += relativedelta(years=1)
            
        item.save()
        messages.info(request, f"🔄 Tekrarlayan işlem otomatik eklendi: {item.title} ({item.amount} {item.currency})")

    # --- C. AKILLI BÜTÇE UYARI ALGORİTMASI (%80 - %100) (Gün 6) ---
    current_month = date.today().month
    current_year = date.today().year
    
    for limit_obj in user_limits:
        category_expenses = user_transactions.filter(
            category=limit_obj.category,
            transaction_type='EXPENSE',
            date__year=current_year,
            date__month=current_month
        )
        
        total_spent = sum([t.try_amount for t in category_expenses], Decimal('0.00'))
        limit_val = limit_obj.monthly_limit
        
        if limit_val > 0:
            percentage = (total_spent / limit_val) * Decimal('100')
            
            if percentage >= 100:
                messages.error(request, f"🚨 DİKKAT! '{limit_obj.category.name}' kategorisindeki aylık bütçe limitinizi aştınız! Harcama: {total_spent:.2f} / Limit: {limit_val} TRY")
            elif percentage >= 80:
                messages.warning(request, f"⚠️ UYARI: '{limit_obj.category.name}' kategorisindeki bütçenizin %80'ine ulaştınız. Harcama: {total_spent:.2f} / Limit: {limit_val} TRY")

    # --- D. TOPLAM GELİR VE GİDERLERİN TRY KARŞILIĞI HESABI (Gün 8) ---
    total_income_try = Decimal('0.00')
    total_expense_try = Decimal('0.00')
    
    for t in user_transactions:
        if t.transaction_type == 'INCOME':
            total_income_try += t.try_amount
        else:
            total_expense_try += t.try_amount

    # --- E. CANLI KURLARI ÇEKME VE CONTEXT'E EKLEME (Gün 8) ---
    rates = get_exchange_rates()
    usd_rate = rates.get('USD', 0)
    eur_rate = rates.get('EUR', 0)

    context = {
        'transactions': user_transactions,
        'user_limits': user_limits,
        'total_income_try': total_income_try,
        'total_expense_try': total_expense_try,
        'usd_rate': usd_rate,
        'eur_rate': eur_rate,
    }
    return render(request, 'tracker/home.html', context)


# 5. İşlem Ekleme (Create)
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


# 6. İşlem Düzenleme (Update)
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


# 7. İşlem Silme (Delete)
@login_required(login_url='login')
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.error(request, "İşlem sistemden silindi.")
        return redirect('home')
        
    return render(request, 'tracker/transaction_confirm_delete.html', {'transaction': transaction})


# 8. Excel Dışa Aktarma (Export)
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


# 9. Excel İçe Aktarma (Import)
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


# 10. Kategori Bütçe Limiti Belirleme Görünümü (Gün 6)
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


# 11. Tekrarlayan İşlem Tanımlama Görünümü (Gün 7)
@login_required(login_url='login')
def recurring_add(request):
    if request.method == 'POST':
        form = RecurringTransactionForm(request.POST)
        if form.is_valid():
            rec_item = form.save(commit=False)
            rec_item.user = request.user
            rec_item.save()
            messages.success(request, "Tekrarlayan işlem başarıyla tanımlandı!")
            return redirect('home')
    else:
        form = RecurringTransactionForm()
        
    return render(request, 'tracker/recurring_form.html', {'form': form})