import logging
import os
import sys
import time
from datetime import datetime
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from attr import exceptions
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'telegram_bot_logger.log')

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format=('%(lineno)s - %(levelname)s - %(message)s'
            ' - %(funcName)s - %(asctime)s')
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=20000000,
    backupCount=2,
)
formatter = logging.Formatter(
    '%(lineno)s - %(levelname)s - %(message)s - %(funcName)s - %(asctime)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram чат, определяемый переменной окружения.
    TELEGRAM_CHAT_ID. Принимает на вход два параметра: экземпляр класса
    Bot и строку с текстом сообщения.
    """
    logger.info('Начало работы функции')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено')
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка {error}')


def get_api_answer(current_timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса. В качестве.
    параметра функция получает временную метку. В случае успешного
    запроса должна вернуть ответ API, преобразовав его из формата
    JSON к типам данных Python
    """
    logger.info('Начало работы функции get_api_answer()')

    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params,
        )
    except requests.RequestException as error:
        message = f'Код ответа API (RequestException): {error}'
        logger.error(msg=message)
    if response.status_code != HTTPStatus.OK:
        message = f'Ошибка доступа {response.status_code} к {ENDPOINT}'
        logger.error(message)
        raise requests.RequestException(message)
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на корректность. В качестве параметра функция.
    получает ответ API, приведенный к типам данных Python. Если ответ
    API соответствует ожиданиям, то функция должна вернуть список
    домашних работ (он может быть и пустым), доступный в ответе
    API по ключу 'homeworks'
    """
    logger.info('Начало работы функции')
    if not isinstance(response, dict):
        message = 'Ошибка: ответ API не является dict!'
        logger.error(msg=message)
        raise TypeError(message)
    if 'homeworks' not in response.keys():
        raise KeyError('В ответе API нет ключа homeworks')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        message = 'Ошибка: homeworks не является list!'
        logger.error(msg=message)
        raise TypeError(message)
    return homeworks


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус.
    этой работы. В качестве параметра функция получает только
    один элемент из списка домашних работ. В случае успеха,
    функция возвращает подготовленную для отправки в Telegram
    строку, содержащую один из вердиктов словаря HOMEWORK_STATUSES.
    """
    logger.info('Начало работы функции')
    if not isinstance(homework, dict):
        raise TypeError('homework не является словарем')
    if 'status' not in homework:
        raise KeyError('homework не содержит ключа status')
    if 'homework_name' not in homework:
        raise KeyError('homework не содержит ключа homework_name')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        message = 'Ошибка статуса HOMEWORK_STATUSES'
        logger.error(message)
        raise KeyError(message)
    return f'Изменился статус проверки работы "{homework_name}" на {verdict}'


def check_tokens():
    """
    Проверяет доступность переменных окружения, которые необходимы для.
     работы программы. Если отсутствует хотя бы одна переменная окружения
      — функция должна вернуть False, иначе — True
    """
    logger.info('Начало работы функции')
    if PRACTICUM_TOKEN is None:
        logger.info('Отсутствует PRACTICUM_TOKEN')
        return False
    if TELEGRAM_TOKEN is None:
        logger.info('Отсутствует TELEGRAM_TOKEN')
        return False
    if TELEGRAM_CHAT_ID is None:
        logger.info('Отсутствует TELEGRAM_CHAT_ID')
        return False
    return True


def main():
    """
    Основная логика работы бота. Последовательность действий:.
    1.Запрос к API. 2.Проверка ответа. 3.Если есть обновления —
    получение статуса работы из обновления и отправка сообщения
    в Telegram. 4. Выдержка и выполнение нового запроса.
    """
    logger.info('Начало работы функции')
    if not check_tokens():
        logger.critical('Отсутствует один или несколько Токенов!')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(datetime.now().timestamp())
    hw_status = ''
    error_message = ''

    while True:
        try:
            logger.debug(f'timestamp = {current_timestamp}')
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                new_hw_status = homeworks[0].get('status')
                if new_hw_status != hw_status:
                    send_message(bot, parse_status(new_hw_status[0]))
                    hw_status = new_hw_status
                    logger.info(
                        ('Статус домашней работы изменился и'
                         ' отправлен в телеграм')
                    )

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            if message != error_message:
                send_message(bot, message)
                error_message = message
        finally:
            logger.debug('Начало ожидания')
            time.sleep(RETRY_TIME)
            current_timestamp = int(datetime.now().timestamp())
            logger.debug(f'Конец ожидания, timestamp = {current_timestamp}')


if __name__ == '__main__':
    main()
