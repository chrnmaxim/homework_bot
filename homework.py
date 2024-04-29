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
    except MessageError('Ошибка при отправке сообщения.') as error:
        logger.error(error)
    else:
        logger.debug('Сообщение успешно отправлено.')


def get_api_answer(timestamp: int) -> dict:
    """
    Запрос к API  Яндекс.Практикум.

    При успешном запросе возвращает ответ API в виде словаря.
    """
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        status = homework_statuses.status_code
    except requests.RequestException() as error:
        logger.error(error)
    if status != HTTPStatus.OK:
        error_message = f'Ошибка ответа API. Полученный статус: {status}.'
        logger.error(error_message)
        raise requests.RequestException(error_message)
    return homework_statuses.json()


def check_response(response: dict) -> dict:
    """
    Проверка ответа API на соответствие документации.

    При успешной проверке возвращает информацию о последней домашней работе.
    """
    if not isinstance(response, dict):
        error_message = 'Полученный от API тип данных не является словарем.'
        logger.error(error_message)
        raise TypeError(error_message)
    homeworks_list = response.get('homeworks')
    if not isinstance(homeworks_list, list):
        error_message = (
            'Полученный от API перечень домашних работ не является списком.'
        )
        logger.error(error_message)
        raise TypeError(error_message)
    if not homeworks_list:
        logger.debug('Статус домашней работы не изменен.')
    else:
        last_homework = homeworks_list[0]
        if not isinstance(last_homework, dict):
            error_message = (
                'Полученный от API тип данных не является словарем.'
            )
            logger.error(error_message)
            raise TypeError(error_message)
        return last_homework


def parse_status(homework: dict) -> str:
    """Извлекает статус последней домашней работы."""
    if 'homework_name' not in homework:
        error_message = 'Ключ "homework_name" отсутствует в словаре homework.'
        logger.error(error_message)
        raise KeyError(error_message)
    elif 'status' not in homework:
        error_message = 'Ключ "status" отсутствует в словаре homework.'
        logger.error(error_message)
        raise KeyError(error_message)
    last_homework_name = homework.get('homework_name')
    last_homework_status = homework.get('status')
    if last_homework_status not in HOMEWORK_VERDICTS:
        error_message = (
            f'Неизвестный статус выполнения работы {last_homework_name}.'
        )
        logger.error(error_message)
        raise KeyError(error_message)
    verdict = HOMEWORK_VERDICTS.get(last_homework_status)
    return (f'Изменился статус проверки работы "{last_homework_name}". '
            f'{verdict}')


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        error_message = (
            'Ошибка переменных окружения, проверьте содержание файла .env.'
        )
        logger.critical(error_message)
        raise EnvVarException(error_message)

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    STATUS_HOME_WORK: str = ''
    STATUS_ERROR_MAIN: str = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if 'current_date' not in response:
                error_message = 'Ключ "current_date" отсутствует в ответе API.'
                logger.error(error_message)
                raise KeyError(error_message)
            current_timestamp = response.get('current_date')
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                if message != STATUS_HOME_WORK:
                    send_message(bot, message)
                    STATUS_HOME_WORK = message
            else:
                logger.debug('Обновление статуса каждые 10 минут')
        except Exception as error:
            logger.error(error)
            message = f'Сбой в работе программы главной функции: {error}'
            if message != STATUS_ERROR_MAIN:
                send_message(bot, message)
                STATUS_ERROR_MAIN = message
            time.sleep(RETRY_PERIOD)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
