# FastAPIProject1 (FinFlow)

## Швидкий старт

### 1) Підготувати `.env`
Скопіюй `.env.example` -> `.env` і за потреби зміни значення.

### 2) Зібрати та запустити все
```powershell
docker compose up --build
```

Після старту:
- Frontend: http://localhost
- Backend: http://localhost:8000
- RabbitMQ UI: http://localhost:15672 (guest/guest)

## AWS S3
- Результати обчислень зберігаються в AWS S3.
- Налаштуй у `.env`: `S3_BUCKET`, `S3_REGION`, `S3_KEY_PREFIX`.
- Креденшіали: або `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (і за потреби `AWS_SESSION_TOKEN`), або IAM Role на інфраструктурі AWS.

Усі сервіси стартують без hot reload. Міграції запускаються автоматично всередині API-контейнера.

