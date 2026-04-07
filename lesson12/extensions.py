import requests
import json

class APIException(Exception):
    """Собственное исключение для ошибок API"""
    pass

class CurrencyConverter:
    """Класс для конвертации валют"""

    @staticmethod
    def get_price(base: str, quote: str, amount: float) -> float:
        """
        Статический метод для получения цены в нужной валюте

        :param base: валюта, цену которой надо узнать
        :param quote: валюта, в которой надо узнать цену
        :param amount: количество переводимой валюты
        :return: сумма в целевой валюте
        """
        # Словарь для нормализации названий валют
        currency_mapping = {
            'доллар': 'USD',
            'евро': 'EUR',
            'рубль': 'RUB'
        }

        # Нормализуем названия валют
        base_code = currency_mapping.get(base.lower())
        quote_code = currency_mapping.get(quote.lower())

        if not base_code:
            raise APIException(f'Неизвестная валюта: {base}')
        if not quote_code:
            raise APIException(f'Неизвестная валюта: {quote}')

        try:
            # Используем бесплатный API для получения курсов валют
            url = f'https://api.exchangerate-api.com/v4/latest/{base_code}'
            response = requests.get(url)
            data = response.json()

            if response.status_code != 200:
                raise APIException('Ошибка при получении данных от API')

            if quote_code not in data['rates']:
                raise APIException(f'Невозможно сконвертировать {base} в {quote}')

            rate = data['rates'][quote_code]
            result = rate * amount
            return round(result, 2)

        except requests.RequestException as e:
            raise APIException(f'Ошибка соединения с API: {e}')
        except json.JSONDecodeError as e:
            raise APIException(f'Ошибка парсинга JSON: {e}')
        except KeyError as e:
            raise APIException(f'Ошибка в данных API: отсутствует ключ {e}')