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
previous_homework = []


ErrorIsNotInTelegram = {
    'URL-адрес недоступен': True,
    'Сбой при обращении к': True,
    'Ключ "homework_name"': True,
    'Ключ "homework_statu': True,
    'Отсутствует документ': True,
    'Сбой при отправке со': True,
    'Сбой в работе програ': True,
}


def get_stream_handler():
    """Обработчик логирования..."""
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    return stream_handler


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(get_stream_handler())


def SendErrorToTelegram(message):
    """Направление ошибки уровня ERROR в Телеграм, если ее там еще нет..."""
    if ErrorIsNotInTelegram[message[:20]]:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        bot.send_message(TELEGRAM_CHAT_ID, message)
        ErrorIsNotInTelegram[message[:20]] = False
    return


def LogErrorAndSendToTelegram(message):
    """Логирование и направление ошибки в Телеграм, если ее там еще нет..."""
    logger.error(message)
    SendErrorToTelegram(message)
    return


def check_tokens():
    """Проверка наличия ключей..."""
    ValuesExist = PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
    if not PRACTICUM_TOKEN:
        logger.critical('Отсутствует обязательная переменная PRACTICUM_TOKEN')
    elif not TELEGRAM_TOKEN:
        logger.critical('Отсутствует обязательная переменная TELEGRAM_TOKEN')
    elif not TELEGRAM_CHAT_ID:
        logger.critical('Отсутствует обязательная переменная TELEGRAM_CHAT_ID')
    else:
        logger.debug('Проверка ключей проведена')
    return bool(ValuesExist)


def get_api_answer(current_timestamp):
    """Направление запроса и получение ответа..."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == 200:
        logger.debug('Ответ от сервера получен')
        return response.json()
    elif response.status_code == 404:
        raise LogErrorAndSendToTelegram('URL-адрес недоступен')
    else:
        raise LogErrorAndSendToTelegram('Сбой при обращении к URL')


def check_response(response):
    """Проверка ответа..."""
    if type(response['homeworks']) == list:
        logger.debug('Проверен тип данных ответа: ОK')
        return response.get('homeworks')
    else:
        logger.info('Ответ не содержит перечень домашних работ')
        raise TypeError


def parse_status(homework):
    """Определение статуса работы..."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_name:
        raise KeyError
    if not homework_status:
        LogErrorAndSendToTelegram('Ключ "homework_status" отсутствует')
        raise KeyError
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if not verdict:
        raise LogErrorAndSendToTelegram(
            'Отсутствует документированный статус'
            f'проверки работы "{homework_name}"'
        )
    logger.info(
        f'Сообщение в Телеграм для "{homework.get("lesson_name")[16:]}"'
        'сформировано...'
    )
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def send_message(bot, message):
    """Направление сообщения в Телеграм..."""
    logger.info('Отправлено')
    bot.send_message(TELEGRAM_CHAT_ID, message)
    if not bot.send_message:
        raise LogErrorAndSendToTelegram(
            'Сбой при отправке сообщения в Телеграм'
        )
    return


def main():
    """Главная функция бота..."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True and check_tokens():
        try:
            global previous_homework
            api_answer = get_api_answer(current_timestamp)
            homework_list = check_response(api_answer)
            if homework_list != previous_homework:
                previous_homework = homework_list
                for homework in homework_list:
                    message = parse_status(homework)
                    send_message(bot, message)
            else:
                logger.debug(
                    'Сообщение в Телеграм не отправлено, обновлений нет'
                )
        except Exception as error:
            raise LogErrorAndSendToTelegram(
                f'Сбой в работе программы: {error}')
        time.sleep(RETRY_TIME)
    return


if __name__ == '__main__':
    main()
