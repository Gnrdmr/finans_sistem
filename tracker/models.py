from django.db import models
from django.contrib.auth.models import User
from datetime import date


# 1. Kategori Modeli
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")

    def __str__(self):
        return self.name


# 2. İşlem Modeli (Gün 8: Döviz Seçenekleri Eklendi)
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Gelir'),
        ('EXPENSE', 'Gider'),
    ]
    
    CURRENCY_CHOICES = [
        ('TRY', 'Türk Lirası (TRY)'),
        ('USD', 'Amerikan Doları (USD)'),
        ('EUR', 'Euro (EUR)'),
    ]

    @property
    def try_amount(self):
        if self.currency == 'TRY':
            return self.amount
        
        # Importu sadece burada, metodun içinde çağırıyoruz:
        from tracker.views import convert_to_try
        
        try:
            converted = convert_to_try(self.amount, self.currency)
            return round(converted, 2)
        except Exception:
            return self.amount

    @try_amount.setter
    def try_amount(self, value):
    # Dışarıdan try_amount = X atandığında bunun amount'a nasıl yansıyacağını belirtiyoruz:
      self.amount = value
      self.currency = 'TRY'  # Varsayılan olarak TL yapabilirsiniz
    

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    title = models.CharField(max_length=150, verbose_name="İşlem Başlığı")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Miktar")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="İşlem Türü")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    date = models.DateField(default=date.today, verbose_name="Tarih")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='TRY', verbose_name="Döviz Cinsi")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")

    due_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)       
    is_subscription = models.BooleanField(default=False)




class TransactionTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100) 
    amount = models.DecimalField(max_digits=10, decimal_places=2) 
    category = models.CharField(max_length=50) 
    
    def __str__(self):
        return f"{self.title} ({self.amount} TRY)"

   






    def __str__(self):
        return f"{self.title} - {self.amount} {self.currency}"


# 3. Kategori Bazlı Bütçe Limiti Modeli (Gün 6)
class BudgetLimit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategori")
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Aylık Bütçe Limiti (TRY)")

    class Meta:
        unique_together = ('user', 'category')

    def __str__(self):
        return f"{self.user.username} - {self.category.name}: {self.monthly_limit} TRY"

class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# 4. Tekrarlayan İşlemler Modeli (Gün 7)
class RecurringTransaction(models.Model):
    INTERVAL_CHOICES = [
        ('DAILY', 'Günlük'),
        ('WEEKLY', 'Haftalık'),
        ('MONTHLY', 'Aylık'),
        ('YEARLY', 'Yıllık'),
    ]

    CURRENCY_CHOICES = [
        ('TRY', 'Türk Lirası (TRY)'),
        ('USD', 'Amerikan Doları (USD)'),
        ('EUR', 'Euro (EUR)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    title = models.CharField(max_length=150, verbose_name="İşlem Başlığı")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Miktar")
    transaction_type = models.CharField(max_length=10, choices=Transaction.TRANSACTION_TYPES, verbose_name="İşlem Türü")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='TRY', verbose_name="Döviz Cinsi")
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, verbose_name="Tekrarlama Sıklığı")
    start_date = models.DateField(default=date.today, verbose_name="Başlangıç Tarihi")
    next_date = models.DateField(verbose_name="Sonraki İşlem Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")

    def __str__(self):
        return f"{self.title} ({self.get_interval_display()})"



    # 5. Ortak Harcama Grubu Modeli (Gün 9)
class ExpenseGroup(models.Model):
    name = models.CharField(max_length=150, verbose_name="Grup Adı")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_groups", verbose_name="Oluşturan")
    members = models.ManyToManyField(User, related_name="expense_groups", verbose_name="Grup Üyeleri")
    created_at = models.DateField(default=date.today, verbose_name="Oluşturulma Tarihi")

    def __str__(self):
        return self.name


# 6. Ortak Harcama Modeli (Gün 9)
class SharedExpense(models.Model):
    group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name="expenses", verbose_name="Harcama Grubu")
    title = models.CharField(max_length=150, verbose_name="Harcama Açıklaması")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar")
    currency = models.CharField(max_length=3, choices=Transaction.CURRENCY_CHOICES, default='TRY', verbose_name="Döviz Cinsi")
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="paid_expenses", verbose_name="Ödeyen Kişi")
    date = models.DateField(default=date.today, verbose_name="Tarih")

    def __str__(self):
        return f"{self.title} - {self.amount} {self.currency} ({self.group.name})"