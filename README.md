# Atol API


Python-пакет для работы с API Atol Web Server.

### Установка

*- Soon*
### Примеры

[Документация](https://integration.atol.ru/api/?python#json_items) (кликабельно) с примерами использования JSON



    # Пример реализован с электронным проведением документа (без печати чека)

    import atol_webapi
    from config import HOST, PORT, CASHIER
    
    atol = atol_webapi.AtolAPI(HOST, PORT, CASHIER)

    # открываем смену
    atol.open_shift(is_web=True)

    items = [
        {
            "type": "position",
            "name": "Бананы",
            "price": 70.50,
            "quantity": 2.0,
            "amount": 141.00, # можно установить 0, функция пересчитает
            "infoDiscountAmount": 0.0,
            "paymentMethod": "fullPrepayment",
            "paymentObject": "commodity",
            "tax": {
                "type": "vat0"
            }
        }
    ]
    
    # создаем печатный чек
    result = atol.new_fiscal_doc("sell", items, tax_type="usnIncomeOutcome", payment_type="electronically", is_web=True)
    
    # выводим результат
    print(result)

    # закрываем смену
    atol.close_shift(is_web=True)

### Для разработчиков
Проект открыт к пул-реквестам, если у вас есть время и желание - you are welcome :)

### Связь
[![Telegram](https://img.shields.io/badge/-TELEGRAM-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/fdnflm)
[![Gmail](https://img.shields.io/badge/-GMAIL-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:fadinflame@gmail.com)