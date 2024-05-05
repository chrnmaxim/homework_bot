import json
import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import EnvVarException, MessageError

load_dotenv()


PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 600
TIMESTAMP_DELTA: int = 30

ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict[str, str] = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS: dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

LOG_FORMAT: str = '%(asctime)s - %(levelname)s - %(message)s - %(funcName)s'

formatter = logging.Formatter(LOG_FORMAT)

handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message) -> None:
    """Отправка сообщений в чат Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except MessageError as error:
        raise Exception(f'Ошибка при отправке сообщения: {error}')
    else:
        logger.debug('Сообщение успешно отправлено.')


def get_api_answer(timestamp: int) -> dict:
    """
    Запрос к API  Яндекс.Практикум.

    При успешном запросе возвращает ответ API в виде словаря.
    """
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=payload
        )
    except requests.RequestException as error:
        raise Exception(f'Сбой при запросе к API: {error}')
    if response.status_code != HTTPStatus.OK:
        error_message = (
            f'Ошибка ответа API. Полученный статус:{response.status_code}.'
        )
        raise Exception(error_message)
    try:
        return response.json()
    except json.decoder.JSONDecodeError as error:
        raise Exception(f'Полученный JSON не валиден: {error}')


def check_response(response: dict) -> dict:
    """
    Проверка ответа API на соответствие документации.

    При успешной проверке возвращает список домашних работ
    и время отправки ответа.
    """
    if not isinstance(response, dict):
        error_message = 'Полученный от API тип данных не является словарем.'
        raise TypeError(error_message)
    if 'homeworks' not in response:
        error_message = 'Ключ "homeworks" отсутствует в ответе API.'
        raise KeyError(error_message)
    homeworks_list = response.get('homeworks')
    if not isinstance(homeworks_list, list):
        error_message = (
            'Полученный от API перечень домашних работ не является списком.'
        )
        raise TypeError(error_message)
    if 'current_date' not in response:
        error_message = 'Ключ "current_date" отсутствует в ответе API.'
        raise KeyError(error_message)
    current_timestamp = response.get('current_date')
    if not isinstance(current_timestamp, int):
        error_message = (
            'Полученный от API формат даты не является int.'
        )
        raise TypeError(error_message)
    return homeworks_list, current_timestamp


def parse_status(homework: dict) -> str:
    """Извлекает статус последней домашней работы."""
    if not isinstance(homework, dict):
        error_message = (
            'Полученный от API тип данных не является словарем.'
        )
        raise TypeError(error_message)
    if 'homework_name' not in homework:
        error_message = 'Ключ "homework_name" отсутствует в словаре homework.'
        raise KeyError(error_message)
    if 'status' not in homework:
        error_message = 'Ключ "status" отсутствует в словаре homework.'
        raise KeyError(error_message)
    if homework.get('status') not in HOMEWORK_VERDICTS:
        error_message = (
            'Неизвестный статус выполнения работы '
            f'{homework.get("homework_name")}.'
        )
        raise KeyError(error_message)
    return ('Изменился статус проверки работы '
            f'"{homework.get("homework_name")}". '
            f'{HOMEWORK_VERDICTS.get(homework.get("status"))}')


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        error_message = (
            'Ошибка переменных окружения, проверьте содержание файла .env.'
        )
        logger.critical(error_message)
        raise EnvVarException(error_message)

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - TIMESTAMP_DELTA

    prev_error: str = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks_list, current_timestamp = check_response(response)
            if homeworks_list:
                message = parse_status(homeworks_list[0])
                send_message(bot, message)
            else:
                logger.debug('Обновление статуса каждые 10 минут.')
            prev_error = ''
        except Exception as error:
            logger.error(error)
            message = f'Сбой в работе программы главной функции: {error}'
            if message != prev_error:
                send_message(bot, message)
                prev_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
