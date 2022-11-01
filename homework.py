import logging
import sys
import os
import time
import requests
import telegram

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


current_timestamp = 1549962000


def get_stream_handler():
    """Обработчик логирования."""
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    return stream_handler


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(get_stream_handler())


def log_and_send_error_to_Telegram(bot, message):
    """Логирование и направление ошибки в Телеграм."""
    logger.error(message)
    send_message(bot, message)


def check_tokens() -> bool:
    """Проверка наличия ключей."""
    if not PRACTICUM_TOKEN:
        logger.critical('Отсутствует обязательная переменная PRACTICUM_TOKEN')
    elif not TELEGRAM_TOKEN:
        logger.critical('Отсутствует обязательная переменная TELEGRAM_TOKEN')
    elif not TELEGRAM_CHAT_ID:
        logger.critical(
            'Отсутствует обязательная переменная TELEGRAM_CHAT_ID')
    else:
        logger.debug('Проверка ключей проведена')
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def get_api_answer(current_timestamp):
    """Направление запроса и получение ответа."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            raise Exception(f'Сбой при обращении к URL {response.request.url}'
                            f'; код ответа: {response.status_code} - '
                            f'{response.reason}; параметры: {params}')
        logger.debug('Ответ от сервера получен')
        response = response.json()
    except TypeError:
        logger.debug('Ответ от сервера не может быть обработан')
    return response


def check_response(response):
    """Проверка ответа."""
    if response['homeworks']:
        logger.debug('Ответ содержит ключ "homeworks"')
    else:
        raise KeyError('В ответе отсутствует ключ "homeworks"')
    if response['current_date']:
        logger.debug('Ответ содержит текущую дату (ключ "current_date")')
    else:
        raise KeyError('Ответ не содержит текущую дату (ключ "current_date")')
    if isinstance(response, dict):
        logger.debug(f'Тип данных ответа правильный: {type(response)}')
    else:
        raise TypeError(f'Неправильный тип данных ответа: {type(response)}')
    if isinstance(response['homeworks'], list):
        logger.debug('Проверен тип данных ответа с ключом "homeworks": '
                     f'{type(response["homeworks"])}')
        return response.get('homeworks')[0]
    else:
        logger.info('Ответ не содержит перечень домашних работ')
        raise TypeError('Неправильный тип данных ответа с ключом "homeworks":'
                        f'{type(response["homeworks"])}')


def parse_status(homework):
    """Определение статуса работы."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует название работы')
    if 'status' not in homework:
        raise KeyError('Отсутствует информация о статусе работы'
                       f'{homework.get("homework_name")}')
    verdict = HOMEWORK_STATUSES.get(homework.get('status'))
    if not verdict:
        raise KeyError('Отсутствует документированный статус'
                       f'проверки работы "{homework.get("homework_name")}"')
    message = ('Изменился статус проверки работы'
               f'"{homework.get("homework_name")}".\n{verdict}')
    logger.info(
        f'Сообщение в Телеграм для "{homework.get("lesson_name")[16:]}" '
        'сформировано...'
    )
    return message


def send_message(bot, message):
    """Направление сообщения в Телеграм..."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logger.error('Сбой при отправке сообщения в Телеграм')
    else:
        logger.info('Отправлено')
    return


def main():
    """Главная функция бота."""
    prior_hw = {}
    prior_error = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True and check_tokens():
        try:
            api_answer = get_api_answer(current_timestamp)
            hw = check_response(api_answer)
            hw_is_changed = hw != prior_hw
            if hw_is_changed:
                message = parse_status(hw)
                send_message(bot, message)
                prior_hw = hw
            else:
                logger.debug(
                    'Сообщение в Телеграм не отправлено, обновлений нет'
                )
        except Exception as error:
            error_was_sent_to_Telegram_before = error == prior_error
            if error_was_sent_to_Telegram_before:
                logger.error(error)
            else:
                log_and_send_error_to_Telegram(bot=bot, message=error)
                prior_error = error
        time.sleep(RETRY_TIME)
    return


if __name__ == '__main__':
    main()
