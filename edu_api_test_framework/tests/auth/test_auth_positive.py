import allure

from framework.payloads import valid_register_payload, valid_login_payload
from framework.assertions import assert_status_code, assert_json_has_keys


@allure.feature("Auth")
@allure.story("Student registration")
def test_student_can_register(auth_service):
    payload = valid_register_payload()

    response = auth_service.register(payload)

    assert_status_code(response, 201)
    data = response.json()
    assert_json_has_keys(data, ["message", "user"])
    assert data["user"]["email"] == payload["email"]


@allure.feature("Auth")
@allure.story("Student login")
def test_student_can_login(auth_service):
    payload = valid_register_payload()
    register_response = auth_service.register(payload)
    assert_status_code(register_response, 201)

    response = auth_service.login(valid_login_payload(payload["email"], payload["password"]))

    assert_status_code(response, 200)
    data = response.json()
    assert_json_has_keys(data, ["access_token", "token_type"])
    assert data["token_type"] == "bearer"
