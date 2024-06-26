# NRCKI Seminar Telegram Notifyer
Это неофициальный бот, который можно подключить к личному или групповому чату и получать уведомления о новых семинарах в следующих тематик НИЦ "Курчатовский Интитут":
* Отдел Т: Эксперименты на токамаках, 
* Инженерно-физические проблемы термоядерных реакторов
* Теория магнитного удержания плазмы
* Инженерно-физический семинар по токамакам.

Помимо автоматического получения уведомлени бот позволяет осуществлять поиск по семинарам, опубликованным на страницах соответствующих тематик. 
Бот поддерживает две команды:  `/last` и `/find`. 
Первая может быть без аргументов, он выдаст последний семинар. Какой выберешь или все четыре. Если написать с числом `/last 3`, то выдаст 3 последних семинара. 

Вторая должна быть с аргументом. Она позволяет искать текст во всех семинарах, какие висят на сайте. Поиск очень простой, ищет строку в строке.

## Installation
Бота можно запустить как в среде Python, так и в Docker.

### Python
Для запуска бота с помощью интерпретатора python достаточно сделать следующее:
```
git clone https://github.com/Mr-Boshi/nrcki_seminar_bot.git
cd nrcki_seminar_bot
cp .env_example .env
pip install -r requirements.txt
```
После этого заполните переменные среды в файл `.env` и запустите бота с помощью
```
python bot.py
```
### Docker
Для того, чтоб запустить бота в Docker создайте файл с названием docker-compose.yaml и поместите в него содержимое одноименного файла из репозитория. Заполните переменные среды и выполните команду
```
docker compose up -d
```

## Environment variables
На данный момент бот поддерживает следующие переменные среды:
*  `bot_token` - токен бота к которому можно подключиться
*  `chat_id` - ID чата в который будут автоматически приходить 
*  `admin_id` - ID администратора которому будут приходить сообщения об оибках (when implemented...)

**Опциональные переменные:**
*  `timer` - количество часов между проверками обновлений на сайте. 1 - ежечасно, 24 - раз в сутки. Должно быть целым. По умолчанию - 1.
*  `rate_limit` - максимальное количество сообщений в секунду, которое разрешается отправлять боту. Должно быть положительным float. Не рекомендуется ставить больше 1. По умолчанию 0.5
*  `silent_start` - выключает приветственно сообщение бота, которое отправляется при его запуске. Должно быть True или False, по умолчанию False

## TO-DO
* Error handling
* Better search
* Fetch News from the main page