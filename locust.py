from locust import HttpUser, task, between
import random


class ApiUser(HttpUser):
    host = "http://app:8000"
    wait_time = between(1, 5)


    @task(2)
    def create_and_go_short_link(self):

        payload = {
            "original_link": f"https://{random.randint(1, 1000000)}"
        }
        with self.client.post("/links/shorten", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                short_url = data.get("short_url").split("/")[-1]
                if short_url:
                    self.client.get(f"/links/{short_url}", allow_redirects=False)
                else:
                    response.failure("Failed: No short URL returned")
            else:
                response.failure(f"Failed: {response.text}")


    @task(1)
    def create_and_get_stats(self):
        payload = {
            "original_link": f"https://{random.randint(1, 1000000)}"
        }
        with self.client.post("/links/shorten", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                short_url = data.get("short_url").split("/")[-1]
                if short_url:
                    self.client.get(f"/links/{short_url}/stats", catch_response=True)
                else:
                    response.failure("Failed: No short URL returned")
            else:
                response.failure(f"Failed: {response.text}")


    @task(2)
    def create_and_search(self):
        original_url = f"https://{random.randint(1, 1000000)}"
        payload = {
            "original_link": original_url
        }
        with self.client.post("/links/shorten", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                short_url = data.get("short_url").split("/")[-1]
                if short_url:
                    payload = {
                        "original_url": original_url
                    }
                    self.client.get(f"/links/search", json=payload, catch_response=True)
                else:
                    response.failure("Failed: No short URL returned")
            else:
                response.failure(f"Failed: {response.text}")

    
    @task(1)
    def create_expired_and_check_stats(self):
        payload = {
            "original_link": f"https://{random.randint(1, 1000000)}",
            "expires_at": "2022-01-01 00:00"
        }
        with self.client.post("/links/shorten", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                self.client.get("/links/expired_stats", catch_response=True)
            else:
                response.failure(f"Failed: {response.text}")