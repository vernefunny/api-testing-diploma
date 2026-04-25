from datetime import datetime, timedelta, timezone
import uuid

import jwt
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.database import Base, engine, get_db, SessionLocal
from app import models, schemas
from app.seed import seed_database


JWT_SECRET = "CHANGE_ME_IN_REAL_PROJECT"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCK_MINUTES = 15

app = FastAPI(
    title="Educational Platform API",
    version="3.0.0",
    description="Demo API with SQLite database, validation and business rules.",
)

app.openapi_version = "3.0.3"

security = HTTPBearer(auto_error=False)
password_hash = PasswordHash.recommended()


def problem_response(status_code: int, title: str, detail: str, code: str, field: str | None = None, errors=None):
    body = {
        "type": f"https://api.edu-demo.local/problems/{code.lower().replace('_', '-')}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "code": code,
    }
    if field:
        body["field"] = field
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body, media_type="application/problem+json")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", []) if x not in {"body", "query", "path"}]
        errors.append({
            "field": ".".join(loc) or "request",
            "code": "VALIDATION_ERROR",
            "message": str(err.get("msg", "Invalid value")),
        })
    return problem_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Request validation failed",
        "One or more fields are invalid.",
        "VALIDATION_ERROR",
        errors=errors,
    )


def raise_problem(status_code: int, title: str, detail: str, code: str, field: str | None = None):
    raise HTTPException(
        status_code=status_code,
        detail={
            "type": f"https://api.edu-demo.local/problems/{code.lower().replace('_', '-')}",
            "title": title,
            "status": status_code,
            "detail": detail,
            "code": code,
            "field": field,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail, media_type="application/problem+json")
    return problem_response(exc.status_code, "HTTP error", str(exc.detail), "HTTP_ERROR")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_access_token(user: models.User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise_problem(status.HTTP_401_UNAUTHORIZED, "Token expired", "Access token has expired.", "TOKEN_EXPIRED")
    except jwt.PyJWTError:
        raise_problem(status.HTTP_401_UNAUTHORIZED, "Invalid token", "Access token is invalid.", "INVALID_TOKEN")


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)):
    if credentials is None:
        raise_problem(status.HTTP_401_UNAUTHORIZED, "Authentication required", "Bearer token is required.", "AUTHENTICATION_REQUIRED")

    payload = decode_token(credentials.credentials)
    user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()

    if not user:
        raise_problem(status.HTTP_401_UNAUTHORIZED, "Invalid token", "User from token was not found.", "INVALID_TOKEN")

    if user.status == "deleted":
        raise_problem(status.HTTP_403_FORBIDDEN, "Account deleted", "User account is deleted.", "ACCOUNT_DELETED")

    if user.status != "active":
        raise_problem(status.HTTP_403_FORBIDDEN, "Account is not active", "User account is not active.", "ACCOUNT_NOT_ACTIVE")

    return user


def public_user(user: models.User):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "birth_date": user.birth_date.isoformat(),
        "age": schemas.calculate_age(user.birth_date),
        "status": user.status,
        "role": user.role,
        "receive_marketing_messages": user.receive_marketing_messages,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def course_to_dict(course: models.Course):
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "price": course.price,
        "is_published": course.is_published,
        "rating": course.rating,
    }


def get_course_or_404(course_id: int, db: Session, only_published: bool = False):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course or (only_published and not course.is_published):
        raise_problem(status.HTTP_404_NOT_FOUND, "Course not found", "Course was not found or is not available.", "COURSE_NOT_FOUND", "course_id")
    return course


@app.get("/health_check")
def health_check():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": "3.0.0"}


@app.post("/api/student/auth/register", status_code=status.HTTP_201_CREATED)
def register_student(payload: schemas.RegisterStudentRequest, response: Response, db: Session = Depends(get_db)):
    email = normalize_email(str(payload.email))

    duplicate = db.query(models.User).filter(models.User.email == email).first()
    if duplicate:
        raise_problem(status.HTTP_409_CONFLICT, "Email already exists", "User with this email already exists.", "DUPLICATE_EMAIL", "email")

    user = models.User(
        email=email,
        password_hash=password_hash.hash(payload.password),
        full_name=payload.full_name,
        birth_date=payload.birth_date,
        status="active",
        role="student",
        receive_marketing_messages=payload.receive_marketing_messages,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response.headers["Location"] = f"/api/student/profile/{user.id}"
    return {"message": "Student registered successfully.", "user": public_user(user)}


@app.post("/api/student/auth/login", response_model=schemas.TokenResponse)
def login_student(payload: schemas.LoginStudentRequest, db: Session = Depends(get_db)):
    email = normalize_email(str(payload.email))
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise_problem(status.HTTP_401_UNAUTHORIZED, "Invalid credentials", "Email or password is invalid.", "INVALID_CREDENTIALS")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise_problem(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts", "Account is temporarily locked.", "ACCOUNT_TEMPORARILY_LOCKED")

    if not password_hash.verify(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCK_MINUTES)
            db.commit()
            raise_problem(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts", "Account is temporarily locked for 15 minutes.", "ACCOUNT_TEMPORARILY_LOCKED")
        db.commit()
        raise_problem(status.HTTP_401_UNAUTHORIZED, "Invalid credentials", "Email or password is invalid.", "INVALID_CREDENTIALS")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"access_token": create_access_token(user), "token_type": "bearer"}


@app.post("/api/student/auth/logout")
def logout_student(user: models.User = Depends(get_current_user)):
    return {"message": "Logged out successfully."}


@app.get("/api/student/profile")
def get_profile(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = public_user(user)
    data["interests"] = [
        {"id": item.interest.id, "name": item.interest.name}
        for item in db.query(models.UserInterest).filter(models.UserInterest.user_id == user.id).all()
    ]
    return data


@app.post("/api/student/profile")
def edit_profile(payload: schemas.EditProfileRequest, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.birth_date is not None:
        user.birth_date = payload.birth_date
    if payload.receive_marketing_messages is not None:
        user.receive_marketing_messages = payload.receive_marketing_messages

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return {"message": "Profile updated successfully.", "user": public_user(user)}


@app.delete("/api/student/profile")
def delete_profile(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.status = "deleted"
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Profile deleted successfully."}


@app.post("/api/student/profile/interests")
def set_interests(payload: schemas.SetInterestsRequest, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    interests = db.query(models.Interest).filter(models.Interest.id.in_(payload.interestIds)).all()

    if len(interests) != len(payload.interestIds):
        raise_problem(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid interests", "One or more interest IDs do not exist.", "INVALID_INTEREST_ID", "interestIds")

    db.query(models.UserInterest).filter(models.UserInterest.user_id == user.id).delete()

    for interest_id in payload.interestIds:
        db.add(models.UserInterest(user_id=user.id, interest_id=interest_id))

    db.commit()
    return {"message": "Interests updated successfully.", "interestIds": payload.interestIds}


@app.get("/api/student/themes")
def get_interests(db: Session = Depends(get_db)):
    items = db.query(models.Interest).all()
    return {"items": [{"id": item.id, "name": item.name} for item in items]}


@app.get("/api/student/unauth/courses")
def get_public_courses(
    min_price: int | None = Query(default=None, ge=0, le=1_000_000),
    max_price: int | None = Query(default=None, ge=0, le=1_000_000),
    q: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    if min_price is not None and min_price < 0:
        raise_problem(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid price", "min_price must be >= 0.", "INVALID_PRICE", "min_price")
    if max_price is not None and max_price < 0:
        raise_problem(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid price", "max_price must be >= 0.", "INVALID_PRICE", "max_price")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise_problem(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid price range", "min_price must be less than or equal to max_price.", "INVALID_PRICE_RANGE")

    query = db.query(models.Course).filter(models.Course.is_published == True)

    if q:
        query = query.filter(models.Course.title.ilike(f"%{q}%"))
    if min_price is not None:
        query = query.filter(models.Course.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Course.price <= max_price)

    courses = query.all()
    return {"items": [course_to_dict(course) for course in courses], "count": len(courses)}


@app.get("/api/student/unauth/courses/{course_id}")
def get_public_course(course_id: int = Path(..., gt=0, le=2147483647), db: Session = Depends(get_db)):
    course = get_course_or_404(course_id, db, only_published=True)
    return course_to_dict(course)


@app.get("/api/student/courses")
def get_student_courses(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    courses = db.query(models.Course).filter(models.Course.is_published == True).all()
    return {"items": [course_to_dict(course) for course in courses]}


@app.post("/api/student/courses/{course_id}/buy", status_code=status.HTTP_201_CREATED)
def buy_course(course_id: int = Path(..., gt=0, le=2147483647), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = get_course_or_404(course_id, db, only_published=True)

    existing = db.query(models.Purchase).filter(
        models.Purchase.user_id == user.id,
        models.Purchase.course_id == course_id,
        models.Purchase.status == "paid",
    ).first()

    if existing:
        raise_problem(status.HTTP_409_CONFLICT, "Course already purchased", "User has already purchased this course.", "COURSE_ALREADY_PURCHASED", "course_id")

    purchase = models.Purchase(
        payment_id=str(uuid.uuid4()),
        user_id=user.id,
        course_id=course_id,
        amount=course.price,
        status="paid",
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    return {
        "message": "Course purchased successfully.",
        "course_id": course_id,
        "payment": {
            "id": purchase.payment_id,
            "status": purchase.status,
            "amount": purchase.amount,
            "currency": "RUB",
        },
    }


@app.post("/api/student/courses/{course_id}/refund")
def refund_course(course_id: int = Path(..., gt=0, le=2147483647), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    purchase = db.query(models.Purchase).filter(
        models.Purchase.user_id == user.id,
        models.Purchase.course_id == course_id,
        models.Purchase.status == "paid",
    ).first()

    if not purchase:
        raise_problem(status.HTTP_409_CONFLICT, "Course is not purchased", "Cannot refund a course that was not purchased.", "COURSE_NOT_PURCHASED", "course_id")

    purchase.status = "refund_pending"
    db.commit()
    return {"message": "Refund request accepted.", "course_id": course_id, "refund_status": "pending"}


@app.get("/api/student/courses/{course_id}/sections")
def get_sections(course_id: int = Path(..., gt=0, le=2147483647), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = get_course_or_404(course_id, db, only_published=True)
    return {"items": [{"id": section.id, "name": section.name} for section in course.sections]}


@app.get("/api/student/courses/{course_id}/sections/{section_id}/lessons")
def get_lessons(course_id: int = Path(..., gt=0, le=2147483647), section_id: int = Path(..., gt=0, le=2147483647), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_course_or_404(course_id, db, only_published=True)
    section = db.query(models.Section).filter(models.Section.id == section_id, models.Section.course_id == course_id).first()

    if not section:
        raise_problem(status.HTTP_404_NOT_FOUND, "Section not found", "Section was not found in this course.", "SECTION_NOT_FOUND", "section_id")

    return {"items": [{"id": lesson.id, "name": lesson.name, "content_type": lesson.content_type} for lesson in section.lessons]}


@app.patch("/api/student/courses/{course_id}/complete-lesson/{lesson_id}")
def complete_lesson(course_id: int = Path(..., gt=0, le=2147483647), lesson_id: int = Path(..., gt=0, le=2147483647), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    purchase = db.query(models.Purchase).filter(
        models.Purchase.user_id == user.id,
        models.Purchase.course_id == course_id,
        models.Purchase.status == "paid",
    ).first()

    if not purchase:
        raise_problem(status.HTTP_403_FORBIDDEN, "Course access denied", "User must purchase the course before completing lessons.", "COURSE_ACCESS_DENIED", "course_id")

    lesson = db.query(models.Lesson).join(models.Section).filter(
        models.Lesson.id == lesson_id,
        models.Section.course_id == course_id,
    ).first()

    if not lesson:
        raise_problem(status.HTTP_404_NOT_FOUND, "Lesson not found", "Lesson was not found in this course.", "LESSON_NOT_FOUND", "lesson_id")

    existing = db.query(models.CompletedLesson).filter(
        models.CompletedLesson.user_id == user.id,
        models.CompletedLesson.course_id == course_id,
        models.CompletedLesson.lesson_id == lesson_id,
    ).first()

    if not existing:
        db.add(models.CompletedLesson(user_id=user.id, course_id=course_id, lesson_id=lesson_id))
        db.commit()

    return {"message": "Lesson completed successfully.", "course_id": course_id, "lesson_id": lesson_id}


@app.post("/api/student/courses/{course_id}/ratings", status_code=status.HTTP_201_CREATED)
def set_course_rating(payload: schemas.SetRatingRequest, course_id: int = Path(..., gt=0, le=2147483647), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_course_or_404(course_id, db, only_published=True)

    purchase = db.query(models.Purchase).filter(
        models.Purchase.user_id == user.id,
        models.Purchase.course_id == course_id,
        models.Purchase.status == "paid",
    ).first()

    if not purchase:
        raise_problem(status.HTTP_403_FORBIDDEN, "Rating is not allowed", "Only users who purchased the course can rate it.", "RATING_NOT_ALLOWED", "course_id")

    rating = db.query(models.CourseRating).filter(
        models.CourseRating.user_id == user.id,
        models.CourseRating.course_id == course_id,
    ).first()

    if not rating:
        rating = models.CourseRating(user_id=user.id, course_id=course_id, rating=payload.rating, comment=payload.comment)
        db.add(rating)
    else:
        rating.rating = payload.rating
        rating.comment = payload.comment

    db.commit()
    db.refresh(rating)

    return {
        "message": "Rating saved successfully.",
        "rating": {
            "id": rating.id,
            "course_id": rating.course_id,
            "user_id": rating.user_id,
            "rating": rating.rating,
            "comment": rating.comment,
        },
    }


@app.get("/api/student/courses/{course_id}/ratings")
def get_course_ratings(course_id: int = Path(..., gt=0, le=2147483647), db: Session = Depends(get_db)):
    get_course_or_404(course_id, db, only_published=True)
    ratings = db.query(models.CourseRating).filter(models.CourseRating.course_id == course_id).all()
    return {
        "items": [
            {"id": r.id, "user_id": r.user_id, "course_id": r.course_id, "rating": r.rating, "comment": r.comment}
            for r in ratings
        ],
        "count": len(ratings),
    }


@app.post("/api/student/courses/{course_id}/complaints", status_code=status.HTTP_201_CREATED)
def create_complaint(payload: schemas.ComplaintRequest, course_id: int = Path(..., gt=0, le=2147483647), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_course_or_404(course_id, db, only_published=True)

    complaint = models.Complaint(
        user_id=user.id,
        course_id=course_id,
        reason=payload.reason,
        text=payload.text,
        link=payload.link,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {
        "message": "Complaint created successfully.",
        "complaint": {
            "id": complaint.id,
            "course_id": complaint.course_id,
            "reason": complaint.reason,
            "text": complaint.text,
            "link": complaint.link,
            "status": complaint.status,
        },
    }


@app.get("/api/student/payments/{payment_id}")
def get_payment(payment_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = db.query(models.Purchase).filter(
        models.Purchase.payment_id == payment_id,
        models.Purchase.user_id == user.id,
    ).first()

    if not payment:
        raise_problem(status.HTTP_404_NOT_FOUND, "Payment not found", "Payment was not found.", "PAYMENT_NOT_FOUND", "payment_id")

    return {
        "id": payment.payment_id,
        "course_id": payment.course_id,
        "amount": payment.amount,
        "status": payment.status,
    }


@app.post("/api/student/payments/{payment_id}/installments", status_code=status.HTTP_201_CREATED)
def create_installment(payment_id: str, payload: schemas.InstallmentRequest, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = db.query(models.Purchase).filter(
        models.Purchase.payment_id == payment_id,
        models.Purchase.user_id == user.id,
    ).first()

    if not payment:
        raise_problem(status.HTTP_404_NOT_FOUND, "Payment not found", "Payment was not found.", "PAYMENT_NOT_FOUND", "payment_id")

    return {
        "message": "Installment request created.",
        "installment": {
            "id": str(uuid.uuid4()),
            "payment_id": payment.payment_id,
            "installments_count": payload.installments_count,
            "installments_term": payload.installments_term,
            "status": "pending",
        },
    }


@app.post("/api/student/support/send-email", status_code=status.HTTP_202_ACCEPTED)
def support_send_email(payload: schemas.SupportEmailRequest):
    return {
        "message": "Support request accepted.",
        "request": {
            "id": str(uuid.uuid4()),
            "reason": payload.reason,
            "text": payload.text,
            "email": str(payload.email),
            "status": "accepted",
        },
    }


@app.get("/debug/users")
def debug_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {"items": [public_user(user) for user in users], "count": len(users)}


@app.get("/debug/db-info")
def debug_db_info(db: Session = Depends(get_db)):
    return {
        "users": db.query(models.User).count(),
        "courses": db.query(models.Course).count(),
        "interests": db.query(models.Interest).count(),
        "purchases": db.query(models.Purchase).count(),
        "ratings": db.query(models.CourseRating).count(),
        "complaints": db.query(models.Complaint).count(),
        "database_file": "edu_api_demo.db",
    }
