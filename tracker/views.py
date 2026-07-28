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
from .utils import convert_to_try, get_exchange_rates 
from .forms import ExpenseGroupForm, SharedExpenseForm
from .models import ExpenseGroup


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


@login_required(login_url='login')
def home(request):
    user_transactions = Transaction.objects.filter(user=request.user)
    user_limits = BudgetLimit.objects.filter(user=request.user)
    
    
    for t in user_transactions:
        t.try_amount = convert_to_try(t.amount, t.currency)

    
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

    
    current_month = date.today().month
    current_year = date.today().year
    
    for limit_obj in user_limits:
        category_expenses = user_transactions.filter(
            category=limit_obj.category,
            transaction_type='Gider',
            date__year=current_year,
            date__month=current_month
        )
        
        total_spent = sum([t.try_amount for t in category_expenses], Decimal('0.00'))
        limit_val = limit_obj.monthly_limit
        
        if limit_val > 0:
            percentage = (total_spent / limit_val) * Decimal('100')
            
            if percentage >= 100:
                messages.error(request, f"🚨 DİKKAT! '{limit_obj.category.name}' kategorisindeki aylık bütçe limitinizi aştınız! Harcama: {total_spent} TRY / Limit: {limit_val} TRY")
            elif percentage >= 80:
                messages.warning(request, f"⚠️ UYARI: '{limit_obj.category.name}' kategorisindeki bütçenizin %80'ine ulaştınız. Harcama: {total_spent} TRY")

    
    total_income_try = Decimal('0.00')
    total_expense_try = Decimal('0.00')
    
    for t in user_transactions:
        if t.transaction_type == 'Gelir' or t.transaction_type == 'INCOME':
            total_income_try += t.try_amount
        else:
            total_expense_try += t.try_amount

    
    net_cash_flow = total_income_try - total_expense_try
    
    if total_income_try > 0:
        savings_rate = (net_cash_flow / total_income_try) * 100
    else:
        savings_rate = Decimal('0.00')

    
    rates = get_exchange_rates()
    usd_rate = rates.get('USD', 0)
    eur_rate = rates.get('EUR', 0)

    context = {
        'transactions': user_transactions.order_by('-date'),
        'user_limits': user_limits,
        'total_income_try': total_income_try,
        'total_expense_try': total_expense_try,
        'net_cash_flow': net_cash_flow,     
        'savings_rate': savings_rate,       
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


@login_required(login_url='login')
def create_expense_group(request):
    if request.method == 'POST':
        form = ExpenseGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            form.save_m2m() 
            messages.success(request, "Ortak harcama grubu başarıyla oluşturuldu!")
            return redirect('home')
    else:
        form = ExpenseGroupForm()
    return render(request, 'tracker/group_form.html', {'form': form})



@login_required(login_url='login')
def add_shared_expense(request):
    if request.method == 'POST':
        form = SharedExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ortak harcama sisteme başarıyla eklendi!")
            return redirect('home')
    else:
        form = SharedExpenseForm()
    return render(request, 'tracker/shared_expense_form.html', {'form': form})


@login_required(login_url='login')
def group_list(request):
    user_groups = ExpenseGroup.objects.filter(members=request.user).distinct()
    return render(request, 'tracker/group_list.html', {'user_groups': user_groups})



@login_required(login_url='login')
def group_detail(request, group_id):
    group = get_object_or_404(ExpenseGroup, pk=group_id, members=request.user)
    expenses = group.expenses.all()
    members = group.members.all()
    member_count = members.count()
    
    
    total_spent = sum([convert_to_try(exp.amount, exp.currency) for exp in expenses])
    
    
    per_person_share = total_spent / member_count if member_count > 0 else Decimal('0.00')
    
    
    member_balances = {}
    for member in members:
        user_paid = sum([
            convert_to_try(exp.amount, exp.currency) 
            for exp in expenses if exp.paid_by == member
        ])
        
        net_balance = user_paid - per_person_share
        member_balances[member] = {
            'paid': user_paid,
            'balance': net_balance
        }

    context = {
        'group': group,
        'expenses': expenses,
        'total_spent': total_spent,
        'per_person_share': per_person_share,
        'member_balances': member_balances,
    }
    return render(request, 'tracker/group_detail.html', context)



# 16. Grup Borçlarını Kapatma / Sıfırlama Görünümü (Gün 10)
@login_required(login_url='login')
def settle_debts(request, group_id):
    group = get_object_or_404(ExpenseGroup, pk=group_id, members=request.user)
    if request.method == 'POST':
        # Gruptaki tüm harcamaları silerek borçları sıfırlıyoruz (netleştirme)
        group.expenses.all().delete()
        messages.success(request, f"'{group.name}' grubundaki tüm borçlar başarıyla kapatıldı ve hesaplar netleştirildi!")
    return redirect('group_detail', group_id=group.id)





@login_required(login_url='login')
def monthly_analytics(request):
    today = date.today()
    current_year_month = (today.year, today.month)
    

    current_month_start = date(today.year, today.month, 1)
    if today.month == 1:
        last_month_start = date(today.year - 1, 12, 1)
        last_month_end = date(today.year - 1, 12, 31)
    else:
        last_month_start = date(today.year, today.month - 1, 1)
        last_month_end = current_month_start - relativedelta(days=1)

    
    user_transactions = Transaction.objects.filter(user=request.user, transaction_type='Gider')

    
    current_expenses = user_transactions.filter(date__gte=current_month_start, date__lte=today)
    current_categories = {}
    for t in current_expenses:
        cat_name = t.category.name if t.category else "Diğer"
        amt = convert_to_try(t.amount, t.currency)
        current_categories[cat_name] = current_categories.get(cat_name, 0) + amt


    last_expenses = user_transactions.filter(date__gte=last_month_start, date__lte=last_month_end)
    last_categories = {}
    for t in last_expenses:
        cat_name = t.category.name if t.category else "Diğer"
        amt = convert_to_try(t.amount, t.currency)
        last_categories[cat_name] = last_categories.get(cat_name, 0) + amt

    
    insights = []
    all_categories = set(list(current_categories.keys()) + list(last_categories.keys()))

    for cat in all_categories:
        curr_val = current_categories.get(cat, 0)
        last_val = last_categories.get(cat, 0)

        if last_val > 0:
            change_percent = ((curr_val - last_val) / last_val) * 100
            if change_percent > 0:
                insights.append({
                    'category': cat,
                    'text': f"Bu ay {cat} harcamaların geçen aya göre %{change_percent:.1f} arttı.",
                    'type': 'danger' # Artış gider için genelde olmuyor (kırmızı)
                })
            elif change_percent < 0:
                saving_percent = abs(change_percent)
                insights.append({
                    'category': cat,
                    'text': f"{cat} harcamalarında geçen aya göre %{saving_percent:.1f} tasarruf ettin!",
                    'type': 'success' # Tasarruf yeşil
                })
        elif curr_val > 0:
            insights.append({
                'category': cat,
                'text': f"Geçen ay hiç yapılmayan {cat} kategorisinde bu ay {curr_val:.2f} TRY harcama yapıldı.",
                'type': 'info'
            })

    context = {
        'insights': insights,
        'current_categories': current_categories,
        'last_categories': last_categories,
    }
    return render(request, 'tracker/monthly_analytics.html', context)