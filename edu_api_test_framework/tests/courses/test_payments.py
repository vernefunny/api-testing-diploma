import allure

from framework.assertions import assert_status_code, assert_problem_error


@allure.feature("Payments")
@allure.story("Get payment")
def test_get_payment_after_course_purchase(authorized_services):
    buy_response = authorized_services["courses"].buy_course(course_id=1)
    assert_status_code(buy_response, 201)
    payment_id = buy_response.json()["payment"]["id"]

    response = authorized_services["payments"].get_payment(payment_id)

    assert_status_code(response, 200)
    assert response.json()["id"] == payment_id


@allure.feature("Payments")
@allure.story("Installments")
def test_create_installment_for_payment(authorized_services):
    buy_response = authorized_services["courses"].buy_course(course_id=1)
    assert_status_code(buy_response, 201)
    payment_id = buy_response.json()["payment"]["id"]

    response = authorized_services["payments"].create_installment(
        payment_id,
        {"installments_count": 12, "installments_term": 6},
    )

    assert_status_code(response, 201)
    assert response.json()["installment"]["status"] == "pending"


@allure.feature("Payments")
@allure.story("Installments validation")
def test_create_installment_with_invalid_count_returns_error(authorized_services):
    buy_response = authorized_services["courses"].buy_course(course_id=1)
    assert_status_code(buy_response, 201)
    payment_id = buy_response.json()["payment"]["id"]

    response = authorized_services["payments"].create_installment(
        payment_id,
        {"installments_count": 1, "installments_term": 6},
    )

    assert_problem_error(response, 422, "VALIDATION_ERROR")
