import allure

from framework.assertions import assert_status_code, assert_problem_error


@allure.feature("Profile")
@allure.story("Get profile")
def test_authorized_user_can_get_profile(authorized_services):
    response = authorized_services["profile"].get_profile()

    assert_status_code(response, 200)
    data = response.json()
    assert "email" in data
    assert "full_name" in data


@allure.feature("Profile")
@allure.story("Edit profile")
def test_authorized_user_can_edit_profile(authorized_services):
    payload = {
        "full_name": "Alexander Updated",
        "birth_date": "1998-09-30",
        "receive_marketing_messages": True,
    }

    response = authorized_services["profile"].edit_profile(payload)

    assert_status_code(response, 200)
    assert response.json()["user"]["full_name"] == payload["full_name"]


@allure.feature("Profile")
@allure.story("Set interests")
def test_authorized_user_can_set_interests(authorized_services):
    response = authorized_services["profile"].set_interests({"interestIds": [1, 2, 3]})

    assert_status_code(response, 200)
    assert response.json()["interestIds"] == [1, 2, 3]


@allure.feature("Profile")
@allure.story("Interests validation")
def test_set_duplicate_interests_returns_validation_error(authorized_services):
    response = authorized_services["profile"].set_interests({"interestIds": [1, 1]})

    assert_problem_error(response, 422, "VALIDATION_ERROR")
