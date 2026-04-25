import allure

from framework.assertions import assert_status_code, assert_problem_error


@allure.feature("Courses")
@allure.story("Public catalog")
def test_public_courses_list_is_available(course_service):
    response = course_service.get_public_courses()

    assert_status_code(response, 200)
    data = response.json()
    assert "items" in data
    assert data["count"] >= 1


@allure.feature("Courses")
@allure.story("Public catalog validation")
def test_invalid_price_range_returns_error(course_service):
    response = course_service.get_public_courses(params={"min_price": 10000, "max_price": 1000})

    assert_problem_error(response, 422, "INVALID_PRICE_RANGE")


@allure.feature("Courses")
@allure.story("Purchase")
def test_authorized_user_can_buy_course(authorized_services):
    response = authorized_services["courses"].buy_course(course_id=1)

    assert_status_code(response, 201)
    data = response.json()
    assert data["course_id"] == 1
    assert data["payment"]["status"] == "paid"


@allure.feature("Courses")
@allure.story("Duplicate purchase")
def test_buy_same_course_twice_returns_conflict(authorized_services):
    first_response = authorized_services["courses"].buy_course(course_id=1)
    assert_status_code(first_response, 201)

    second_response = authorized_services["courses"].buy_course(course_id=1)

    assert_problem_error(second_response, 409, "COURSE_ALREADY_PURCHASED")


@allure.feature("Courses")
@allure.story("Learning")
def test_complete_lesson_after_purchase(authorized_services):
    buy_response = authorized_services["courses"].buy_course(course_id=1)
    assert_status_code(buy_response, 201)

    response = authorized_services["courses"].complete_lesson(course_id=1, lesson_id=1)

    assert_status_code(response, 200)
    assert response.json()["lesson_id"] == 1


@allure.feature("Courses")
@allure.story("Rating")
def test_set_rating_after_purchase(authorized_services):
    buy_response = authorized_services["courses"].buy_course(course_id=1)
    assert_status_code(buy_response, 201)

    response = authorized_services["courses"].set_rating(
        course_id=1,
        payload={"rating": 5.0, "comment": "Good course"},
    )

    assert_status_code(response, 201)
    assert response.json()["rating"]["rating"] == 5.0
