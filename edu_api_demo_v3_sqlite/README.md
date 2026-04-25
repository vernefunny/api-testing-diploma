# Edu API Demo v3 SQLite

Версия API с настоящей SQLite-базой для диплома.

## Что появилось

- файл базы `edu_api_demo.db`;
- таблицы `users`, `courses`, `interests`, `purchases`, `completed_lessons`, `course_ratings`, `complaints`;
- стартовое заполнение курсов и интересов;
- пользователи сохраняются после перезапуска сервера;
- можно смотреть базу через DB Browser for SQLite или VS Code SQLite Viewer.

## Запуск

```powershell
cd E:\edu_api_demo_v3_sqlite
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Файл базы появится в корне проекта:

```text
edu_api_demo.db
```

## Как посмотреть базу

### Вариант 1. DB Browser for SQLite

1. Установи DB Browser for SQLite.
2. Открой файл `edu_api_demo.db`.
3. Перейди во вкладку `Browse Data`.
4. Выбирай таблицы: `users`, `courses`, `interests`, `purchases`.

### Вариант 2. VS Code

1. Поставь расширение SQLite Viewer.
2. Открой файл `edu_api_demo.db`.

## Технические debug-ручки

```text
GET /debug/users
GET /debug/db-info
```

Они нужны только для демонстрации и проверки. В реальном проде такие ручки наружу не выставляют, если у компании нет тайной мечты получить утечку данных.

## Пример регистрации

```json
{
  "email": "student@example.com",
  "password": "Password1!",
  "password_confirmation": "Password1!",
  "full_name": "Alexander Petrov",
  "birth_date": "2000-09-30",
  "receive_marketing_messages": false
}
```
