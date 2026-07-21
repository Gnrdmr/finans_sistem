from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Etiket Adı")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Etiket"
        verbose_name_plural = "Etiketler"


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('INCOME', 'Gelir'),
        ('EXPENSE', 'Gider'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    title = models.CharField(max_length=200, verbose_name="İşlem Başlığı")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Miktar")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="İşlem Türü")
    date = models.DateField(verbose_name="Tarih")
    currency = models.CharField(max_length=10, default="TRY", verbose_name="Doviz Cinsi")
    
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Etiketler")
    
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")

    def __str__(self):
        return f"{self.title} - {self.amount} {self.currency} ({self.get_transaction_type_display()})"

    class Meta:
        verbose_name = "İşlem"
        verbose_name_plural = "İşlemler"

class BudgetLimit(models.Model):
      user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
      category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategori")
      monthly_limit = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Aylık Limit (TRY)")
    
      class Meta:
        verbose_name = "Kategori Bütçe Limiti"
        verbose_name_plural = "Kategori Bütçe Limitleri"
        unique_together = ('user', 'category')  # Bir kullanıcının bir kategoride tek limiti olabilir


      def __str__(self):
        return f"{self.user.username} - {self.category.name}: {self.monthly_limit} TRY"    


class RecurringTransaction(models.Model):
    INTERVAL_CHOICES = [
        ('DAILY', 'Günlük'),
        ('WEEKLY', 'Haftalık'),
        ('MONTHLY', 'Aylık'),
        ('YEARLY', 'Yıllık'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    title = models.CharField(max_length=150, verbose_name="İşlem Adı")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar")
    transaction_type = models.CharField(max_length=10, choices=[('INCOME', 'Gelir'), ('EXPENSE', 'Gider')], verbose_name="Tür")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    currency = models.CharField(max_length=3, default='TRY', verbose_name="Para Birimi")
    
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='MONTHLY', verbose_name="Tekrar Sıklığı")
    start_date = models.DateField(verbose_name="Başlangıç Tarihi")
    next_date = models.DateField(verbose_name="Sonraki İşlem Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")

    class Meta:
        verbose_name = "Tekrarlayan İşlem"
        verbose_name_plural = "Tekrarlayan İşlemler"

    def __str__(self):
        return f"{self.title} - {self.amount} {self.currency} ({self.get_interval_display()})"    