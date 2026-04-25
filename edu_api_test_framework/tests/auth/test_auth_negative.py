import allure
import pytest

from framework.payloads import valid_register_payload, valid_login_payload
from framework.assertions import assert_problem_error, assert_status_code


@allure.feature("Auth")
@allure.story("Registration validation")
@pytest.mark.negative
@pytest.mark.parametrize(
    "field,value",
    [
        ("password", "Pass1!"),
        ("password", "Password1"),
        ("password", "Password!"),
        ("birth_date", "2015-01-01"),
        ("birth_date", "1800-01-01"),
    ],
)
def test_register_validation_errors(auth_service, field, value):
    payload = valid_register_payload()
    payload[field] = value

    if field == "password":
        payload["password_confirmation"] = value

    response = auth_service.register(payload)

    assert_problem_error(response, 422, "VALIDATION_ERROR")


@allure.feature("Auth")
@allure.story("Duplicate email")
@pytest.mark.negative
def test_register_duplicate_email(auth_service):
    payload = valid_register_payload()
    first_response = auth_service.register(payload)
    assert_status_code(first_response, 201)

    second_response = auth_service.register(payload)

    assert_problem_error(second_response, 409, "DUPLICATE_EMAIL")


@allure.feature("Auth")
@allure.story("Invalid login")
@pytest.mark.negative
def test_login_with_wrong_password(auth_service, registered_user):
    response = auth_service.login(
        valid_login_payload(
            email=registered_user["email"],
            password="WrongPassword1!",
        )
    )

    assert_problem_error(response, 401, "INVALID_CREDENTIALS")
