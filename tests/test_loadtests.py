# Import the necessary libraries
import requests
from google.oauth2 import service_account
from locust import HttpUser, task
import yaml


# Define a Locust class that specifies the behavior of the load test
class CloudRunLocust(HttpUser):
    def _get_bearer_token(self):
        credentials = service_account.IDTokenCredentials.from_service_account_file(
            self.data["SERVICE_ACCOUNT_KEY_FILE"],
            target_audience=self.data["SERVICE_URL"],
        )

        # get jwt byte token
        jwt_byte = credentials._make_authorization_grant_assertion()
        jwt_string = jwt_byte.decode("utf-8")

        # Send a request to the OAuth2 token endpoint to get an access token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_string,
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        # Extract the access token from the response
        access_token = response.json()["id_token"]

        return access_token

    def on_start(self):
        """on_start is called when a Locust start before any task is scheduled"""
        # load config file
        with open("./config/locust.yml", "r") as file:
            self.data = yaml.safe_load(file)
        self.token = self._get_bearer_token()
        self.headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }

    @task
    def post_request(self):
        """@task decorator specifies this method as a task that locust can execute"""
        self.client.post(
            self.data["SERVICE_URL"] + "/v1/eco-route",
            json={
                "origin": "longmeadow, ma",
                "destination": "brighton, ma",
                "food_preference": "pizza",
                "ev_range": 25000,
            },
            headers=self.headers,
        )
