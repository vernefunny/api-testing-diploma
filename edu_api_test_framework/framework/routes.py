class Routes:
    HEALTH = "/health_check"
    VERSION = "/version"

    REGISTER = "/api/student/auth/register"
    LOGIN = "/api/student/auth/login"
    LOGOUT = "/api/student/auth/logout"

    PROFILE = "/api/student/profile"
    PROFILE_INTERESTS = "/api/student/profile/interests"

    PUBLIC_COURSES = "/api/student/unauth/courses"
    PUBLIC_COURSE_BY_ID = "/api/student/unauth/courses/{course_id}"

    STUDENT_COURSES = "/api/student/courses"
    BUY_COURSE = "/api/student/courses/{course_id}/buy"
    REFUND_COURSE = "/api/student/courses/{course_id}/refund"
    COMPLETE_LESSON = "/api/student/courses/{course_id}/complete-lesson/{lesson_id}"
    COURSE_RATINGS = "/api/student/courses/{course_id}/ratings"
    COURSE_COMPLAINTS = "/api/student/courses/{course_id}/complaints"

    PAYMENT_BY_ID = "/api/student/payments/{payment_id}"
    CREATE_INSTALLMENT = "/api/student/payments/{payment_id}/installments"
