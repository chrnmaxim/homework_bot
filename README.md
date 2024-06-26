# Telegram бот «practicum_final_bot»

### Описание
**Telegram-бот** обращается к API сервису Яндекс.Практикум и узнает статус домашней работы пользователя: взята ли работа в ревью, проверена ли она, а если проверена — принял её ревьюер или же вернул на доработку.

Что делает бот:
* раз в 10 минут опрашивает API сервиса Яндекс.Практикум и проверяет статус последней отправленной на ревью работы;
* при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
* логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

### Технологии:
* Python 3.11
* python-dotenv 0.19.0
* python-telegram-bot 13.7
* requests 2.26.0

### Запуск проекта
Клонировать проект c GitHub:
```
git clone git@github.com:chrnmaxim/homework_bot.git
```
Установить виртуальное окружение:
```
python -m venv venv
```
Активировать виртуальное окружениe:
```
. venv/Scripts/activate
```
Обновить менеджер пакетов pip:
```
python -m pip install --upgrade pip
```
Установить зависимости из requirements.txt:
```
pip install -r requirements.txt
``` 
Запуск бота:
```
python homework.py
```

### **Дополнительная информация**
Перед запуском Telegram-бота необходимо создать переменные окружения в файле **.env**.
```

PRACTICUM_TOKEN = Токен для доступа к данным Яндекс.Практикум
TELEGRAM_TOKEN = API токен бота
TELEGRAM_CHAT_ID = id чата
```

**PRACTICUM_TOKEN** - доступ к API Яндекс.Практикум возможен только по токену. Получить токен можно по [ссылке](https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a) при условии, что выполнен вход в учетную запись Яндекс.Практикум.

**TELEGRAM_TOKEN** - API токен личного бота необходимо получить у телеграм-бота [BotFather](https://t.me/BotFather).

**TELEGRAM_CHAT_ID** - id чата получаем путем отправки сообщения в телеграм-бота [userinfobot](https://t.me/userinfobot).

---
