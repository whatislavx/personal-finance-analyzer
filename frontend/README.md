# FinFlow Frontend (React)

Це React-клієнт для FastAPI бекенду.

## Фічі (Labs)
- Lab 7: React як клієнт (REST = source of truth)
  - створення job
  - список job
  - статуси
  - відновлення стану після refresh
- Lab 8: Real-time (WebSocket)
  - WS client з JWT
  - reconnect/backoff
  - fallback на REST polling

## Налаштування
За замовчуванням фронтенд очікує бекенд:
- REST: `http://localhost:8000`
- WS: `ws://localhost:8000`

Можна перевизначити через Vite env:
- `VITE_API_BASE`
- `VITE_WS_BASE`

## Запуск (Windows / PowerShell)
```powershell
cd C:\Users\Asus\PycharmProjects\FastAPIProject1\frontend
npm install
npm run dev
```

## Логін/Реєстрація
- Sign up: створює користувача через `POST /users/`
- Log in: отримує JWT через `POST /token`

Токен зберігається в `localStorage` під ключем `access_token`.

