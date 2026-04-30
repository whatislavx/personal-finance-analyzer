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
- MinIO UI: http://localhost:9001

Усі сервіси стартують без hot reload. Міграції запускаються автоматично всередині API-контейнера.

