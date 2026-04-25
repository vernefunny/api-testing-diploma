import allure


def assert_status_code(response, expected_code: int) -> None:
    with allure.step(f"Check status code is {expected_code}"):
        assert response.status_code == expected_code, (
            f"Expected status {expected_code}, got {response.status_code}. "
            f"Response body: {response.text}"
        )


def assert_json_has_keys(data: dict, keys: list[str]) -> None:
    with allure.step(f"Check response has keys: {keys}"):
        for key in keys:
            assert key in data, f"Key '{key}' not found in response: {data}"


def assert_problem_error(response, expected_status: int, expected_code: str) -> None:
    assert_status_code(response, expected_status)
    data = response.json()

    with allure.step(f"Check error code is {expected_code}"):
        assert data["status"] == expected_status
        assert data["code"] == expected_code
        assert "title" in data
        assert "detail" in data
