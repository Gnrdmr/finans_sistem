import requests
from django.core.cache import cache
from decimal import Decimal

def get_exchange_rates():
    rates = cache.get('exchange_rates')
    
    if rates is None:
        try:
            # Frankfurter API (TRY bazlı güncel kurlar)
            url = "https://api.frankfurter.app/latest?from=TRY"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                raw_rates = data.get('rates', {})
                base_rates = {'TRY': 1.0}
                for currency, val in raw_rates.items():
                    if val > 0:
                        base_rates[currency] = 1.0 / val
                rates = base_rates
                cache.set('exchange_rates', rates, 3600) # 1 saat önbellekte sakla
            else:
                rates = {'TRY': 1.0, 'USD': 34.0, 'EUR': 37.0}
        except Exception:
            rates = {'TRY': 1.0, 'USD': 34.0, 'EUR': 37.0}
            
    return rates

def convert_to_try(amount, currency):
    rates = get_exchange_rates()
    rate = rates.get(currency, 1.0)
    return amount * Decimal(str(rate))