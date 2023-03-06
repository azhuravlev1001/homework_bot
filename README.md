# Telegram-бот
## _Статус домашнего задания в Телеграме_
Бот обращается к API сервиса Практикум.Домашка и узнает статус домашней работы: взята ли домашка в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

На серверах Практикума есть API, через который можно отслеживать изменение статуса вашей домашней работы, отправленной на ревью.
У API Практикум.Домашка есть лишь один эндпоинт: https://practicum.yandex.ru/api/user_api/homework_statuses/ и доступ к нему возможен только по токену.
Получить токен можно по адресу: https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a.
#### Принцип работы API
Когда ревьюер проверяет вашу домашнюю работу, он присваивает ей один из статусов: 
- работа принята на проверку,
- работа возвращена для исправления ошибок,
- работа принята.

Если работа уже отправлена, но ревьюер пока не взял её на проверку, то это значит, что никакого статуса ей ещё не присвоено. 
С помощью API можно получить список ваших домашних работ, с актуальными статусами за период от `from_date` до настоящего момента. История смены статусов через API недоступна: новый статус всегда перезаписывает старый.

Для успешного запроса нужно: 
- в заголовке запроса передать токен авторизации Authorization: OAuth <token>;
- в GET-параметре `from_date` передать метку времени в формате Unix time.

#### Пример запроса
```
import requests

from pprint import pprint

url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': 'OAuth <ваш токен>'}
payload = {'from_date': <временная метка в формате Unix time>}

# Делаем GET-запрос к эндпоинту url с заголовком headers и параметрами params
homework_statuses = requests.get(url, headers=headers, params=payload)

# Печатаем ответ API в формате JSON
# print(homework_statuses.text)

# А можно ответ в формате JSON привести к типам данных Python и напечатать и его
pprint(homework_statuses.json())
```
Если в запросе переданы валидный токен и временная метка, то после выполнения программы в терминале будет напечатан ответ API.
#### Примеры ответов API
API Практикум.Домашка возвращает ответы в формате JSON. 
В случае успешного запроса (код ответа сервера 200) в ответе должны вернуться два ключа:

- `homeworks`: значение этого ключа — список домашних работ;
- `current_date`: значение этого ключа — время отправки ответа.

В список `homeworks` попадают работы, которым был присвоен статус за период от `from_date` до настоящего момента. Следовательно, с помощью метки времени можно управлять содержанием этого списка: 

- при `from_date = 0` в этот список попадут все ваши домашние работы;
- при `from_date`, равном «минуту назад», велик шанс получить пустой список;
- при других значениях этого параметра в списке будет ограниченный перечень домашних работ.
```
{
   "homeworks":[
      {
         "id":124,
         "status":"rejected",
         "homework_name":"username__hw_python_oop.zip",
         "reviewer_comment":"Код не по PEP8, нужно исправить",
         "date_updated":"2020-02-13T16:42:47Z",
         "lesson_name":"Итоговый проект"
      },
      {
         "id":123,
         "status":"approved",
         "homework_name":"username__hw_test.zip",
         "reviewer_comment":"Всё нравится",
         "date_updated":"2020-02-11T14:40:57Z",
         "lesson_name":"Тестовый проект"
      },

      ...

   ],
   "current_date":1581604970
}
```
#### Действия бота:
- раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет вам соответствующее уведомление в Telegram;
- логирует свою работу и уведомляет вас о важных проблемах сообщением в Telegram.

## Установка и настройки
### Создать аккаунт Telegram-бота
### Зарегистрировать бота
### Настроить аккаунт бота 
###### _Настроить аккаунт бота можно через @BotFather_
### Клонировать репозиторий
```
git clone git@github.com:azhuravlev1001/homework_bot.git
```
### Активация виртуального окружения:
```
cd homework_bot
source venv/Scripts/activate
```
### Установка зависимостей из файла requirements.txt:
```
pip install -r requirements.txt
```
### Запуск тестов:
```
pytest
```
### Запуск проекта:
```
py homework.py
```
## Разработчик:
- Алексей Журавлев
