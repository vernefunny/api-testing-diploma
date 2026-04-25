from __future__ import annotations

import requests
import allure

from framework.config import BASE_URL, REQUEST_TIMEOUT


class ApiClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: str | None = None

    def set_token(self, token: str) -> None:
        self.token = token

    def clear_token(self) -> None:
        self.token = None

    def _headers(self, headers: dict | None = None) -> dict:
        result = {"Accept": "application/json"}
        if headers:
            result.update(headers)
        if self.token:
            result["Authorization"] = f"Bearer {self.token}"
        return result

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = self._headers(kwargs.pop("headers", None))

        with allure.step(f"{method.upper()} {path}"):
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )
            allure.attach(
                f"{method.upper()} {url}\n\nStatus: {response.status_code}\n\n{response.text}",
                name="HTTP response",
                attachment_type=allure.attachment_type.TEXT,
            )
            return response

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
