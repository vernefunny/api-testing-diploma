from datetime import datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="student", nullable=False)
    receive_marketing_messages: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="user")
    interests: Mapped[list["UserInterest"]] = relationship(back_populates="user")


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", "interest_id", name="uq_user_interest"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    interest_id: Mapped[int] = mapped_column(ForeignKey("interests.id"), nullable=False)

    user: Mapped[User] = relationship(back_populates="interests")
    interest: Mapped[Interest] = relationship()


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    sections: Mapped[list["Section"]] = relationship(back_populates="course")


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    course: Mapped[Course] = relationship(back_populates="sections")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="section")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), default="video", nullable=False)

    section: Mapped[Section] = relationship(back_populates="lessons")


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_user_course_purchase"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="paid", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="purchases")
    course: Mapped[Course] = relationship()


class CompletedLesson(Base):
    __tablename__ = "completed_lessons"
    __table_args__ = (UniqueConstraint("user_id", "course_id", "lesson_id", name="uq_completed_lesson"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CourseRating(Base):
    __tablename__ = "course_ratings"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_user_course_rating"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
