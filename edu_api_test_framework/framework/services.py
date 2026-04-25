from framework.api_client import ApiClient
from framework.routes import Routes


class AuthService:
    def __init__(self, client: ApiClient):
        self.client = client

    def register(self, payload: dict):
        return self.client.post(Routes.REGISTER, json=payload)

    def login(self, payload: dict):
        return self.client.post(Routes.LOGIN, json=payload)

    def logout(self):
        return self.client.post(Routes.LOGOUT)


class ProfileService:
    def __init__(self, client: ApiClient):
        self.client = client

    def get_profile(self):
        return self.client.get(Routes.PROFILE)

    def edit_profile(self, payload: dict):
        return self.client.post(Routes.PROFILE, json=payload)

    def set_interests(self, payload: dict):
        return self.client.post(Routes.PROFILE_INTERESTS, json=payload)


class CourseService:
    def __init__(self, client: ApiClient):
        self.client = client

    def get_public_courses(self, params: dict | None = None):
        return self.client.get(Routes.PUBLIC_COURSES, params=params)

    def get_public_course(self, course_id: int):
        return self.client.get(Routes.PUBLIC_COURSE_BY_ID.format(course_id=course_id))

    def get_student_courses(self):
        return self.client.get(Routes.STUDENT_COURSES)

    def buy_course(self, course_id: int):
        return self.client.post(Routes.BUY_COURSE.format(course_id=course_id))

    def refund_course(self, course_id: int):
        return self.client.post(Routes.REFUND_COURSE.format(course_id=course_id))

    def complete_lesson(self, course_id: int, lesson_id: int):
        return self.client.patch(Routes.COMPLETE_LESSON.format(course_id=course_id, lesson_id=lesson_id))

    def set_rating(self, course_id: int, payload: dict):
        return self.client.post(Routes.COURSE_RATINGS.format(course_id=course_id), json=payload)

    def create_complaint(self, course_id: int, payload: dict):
        return self.client.post(Routes.COURSE_COMPLAINTS.format(course_id=course_id), json=payload)


class PaymentService:
    def __init__(self, client: ApiClient):
        self.client = client

    def get_payment(self, payment_id: str):
        return self.client.get(Routes.PAYMENT_BY_ID.format(payment_id=payment_id))

    def create_installment(self, payment_id: str, payload: dict):
        return self.client.post(Routes.CREATE_INSTALLMENT.format(payment_id=payment_id), json=payload)
