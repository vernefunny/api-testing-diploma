import allure

from framework.routes import Routes
from framework.assertions import assert_status_code


@allure.feature("Service")
@allure.story("Health check")
def test_health_check(api_client):
    response = api_client.get(Routes.HEALTH)

    assert_status_code(response, 200)
    assert response.json()["status"] == "ok"
