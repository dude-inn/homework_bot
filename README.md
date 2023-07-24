### Бот Telegram. API_telegram_bot
## Данный проект представляет собой бот в telegram, который сообщает о статусе проверки домашнего задания. Если ревьюер отклонил или же принял проект, отправляется информационное сообщение лично мне в telegram. Реализовано логирование операций.

Развертывание проекта
Зайдите в GitBash, при необходимости установите
При помощи команд
Перейти в каталог:

cd "каталог"
Подняться на уровень вверх:

cd .. 
❗ Перейдите в нужный каталог для клонирования репозитория ❗

Клонирование репозитория:
git clone https://github.com/dude-inn/homework_bot
Перейти в каталог:
cd API_telegram_bot
Создание виртуальной среды:
python -m venv venv 
Активация виртуальной среды:
source venv/Scripts/activate
Установить зависимости из файла requirements.txt:
python -m pip install --upgrade pip
pip install -r requirements.txt
Ввести соответствующие токены в env:
export PRAKTIKUM_TOKEN=***
export TELEGRAM_TOKEN =***
export CHAT_ID=***
Запуск проекта:
python homework.py

Системные требования
Python 3.7.3

GitBash
