import uuid
from locust import HttpUser, task, between
from locust.exception import StopUser

class FinanceUser(HttpUser):
    wait_time = between(1, 5)

    host = "http://localhost:8000"

    def on_start(self):
        suffix = uuid.uuid4().hex[:8]
        username = f"locust_{suffix}"
        password = "LocustPass123!"
        email = f"{username}@example.com"

        create_response = self.client.post(
            "/api/users/",
            json={
                "username": username,
                "email": email,
                "password": password,
            },
        )

        if create_response.status_code != 201:
            print(f"Не вдалося створити користувача: {create_response.status_code}")
            raise StopUser()

        login_response = self.client.post(
            "/api/token",
            data={
                "username": username,
                "password": password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if login_response.status_code != 200:
            print(f"Не вдалося авторизуватися: {login_response.status_code}")
            raise StopUser()

        token = login_response.json().get("access_token")
        if not token:
            print("Не вдалося отримати access_token")
            raise StopUser()

        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(1)
    def get_transactions(self):
        """Тестування отримання фінансових даних (Read)"""
        with self.client.get("/api/financial-data/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status: {response.status_code}")

    @task(3)
    def create_transaction(self):
        """Тестування створення транзакції (Write) - пріоритет вище"""
        self.client.post(
            "/api/financial-data/",
            json={
                "amount": 100.0,
                "category": "Food",
                "type": "EXPENSE",
                "description": f"Test-Locust-{uuid.uuid4().hex[:6]}",
            }
        )
