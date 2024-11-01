# Kindler -- отправка HTML страниц на Amazon Kindle
Этот сервис скачивает содержимое страницы в виде HTML, конвертирует в epub и отправляет на устройство при помощи email на адрес Send to Kindle.
# Запуск сервера
## В контейнере
``` shell
docker build -f Dockerfile -t kindler:latest .
docker run --rm --detach --name kindler -p 8000:8000 \
    -e EMAIL_ADDRESS="email@gmail.com" \
    -e EMAIL_PASSWORD="password" \
    -e KINDLE_EMAIL="kindle-email@gmail.com" \
    kindler:latest
```
Работа проверялась с Gmail, в качестве `EMAIL_PASSWORD` использовать пароль приложения. Переменная `KINDLE_EMAIL` это адрес, на который Amazon принимает файлы для отправки на Kindle.
## Отправка запроса на загрузку статьи
Пример запроса:
``` shell
curl -X POST "http://127.0.0.1:8000/send-article" -H "Content-Type: application/json" -d '{"url": "https://threedots.tech/post/making-games-in-go"}'
```
Пример ответа в случае успеха:
``` json
{"status":"success","message":"Article 'Making_Games_in_Go_for_Absolute_Beginners___Three_Dots_Labs_blog' sent to Kindle."}
```

## Очистка файлов
Пример запроса:
``` shell
curl -X POST "http://127.0.0.1:8000/cleanup"
```
Пример ответа в случае успеха:
``` json
{"status": "success", "message": "All files deleted from SENDS_FOLDER."}
```

## История версий
### [2024-11-01]
Первоначальная версия.