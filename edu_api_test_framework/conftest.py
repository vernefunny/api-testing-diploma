import pytest

from framework.api_client import ApiClient
from framework.payloads import valid_register_payload, valid_login_payload
from framework.services import AuthService, ProfileService, CourseService, PaymentService
from framework.assertions import assert_status_code


@pytest.fixture
def api_client():
    return ApiClient()


@pytest.fixture
def auth_service(api_client):
    return AuthService(api_client)


@pytest.fixture
def course_service(api_client):
    return CourseService(api_client)


@pytest.fixture
def registered_user(auth_service):
    payload = valid_register_payload()
    response = auth_service.register(payload)
    assert_status_code(response, 201)
    return {
        "email": payload["email"],
        "password": payload["password"],
        "register_response": response.json(),
    }


@pytest.fixture
def authorized_client(api_client, registered_user):
    auth = AuthService(api_client)
    login_response = auth.login(
        valid_login_payload(
            email=registered_user["email"],
            password=registered_user["password"],
        )
    )
    assert_status_code(login_response, 200)
    token = login_response.json()["access_token"]
    api_client.set_token(token)
    return api_client


@pytest.fixture
def authorized_services(authorized_client):
    return {
        "auth": AuthService(authorized_client),
        "profile": ProfileService(authorized_client),
        "courses": CourseService(authorized_client),
        "payments": PaymentService(authorized_client),
    }
