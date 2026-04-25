from sqlalchemy.orm import Session

from app import models


def seed_database(db: Session) -> None:
    if db.query(models.Interest).count() == 0:
        db.add_all([
            models.Interest(id=1, name="QA"),
            models.Interest(id=2, name="Python"),
            models.Interest(id=3, name="API Testing"),
            models.Interest(id=4, name="Postman"),
            models.Interest(id=5, name="Automation"),
        ])

    if db.query(models.Course).count() == 0:
        course_1 = models.Course(
            id=1,
            title="Python API Testing",
            description="REST API testing with pytest, requests, Schemathesis and Allure.",
            price=15000,
            is_published=True,
            rating=4.7,
        )
        course_2 = models.Course(
            id=2,
            title="Manual QA Fundamentals",
            description="Checklists, test cases, bug reports and test design.",
            price=9000,
            is_published=True,
            rating=4.5,
        )
        course_3 = models.Course(
            id=3,
            title="Hidden Draft Course",
            description="Unpublished course for negative API checks.",
            price=12000,
            is_published=False,
            rating=0.0,
        )
        db.add_all([course_1, course_2, course_3])
        db.flush()

        section_1 = models.Section(id=1, course_id=1, name="REST API basics")
        section_2 = models.Section(id=2, course_id=2, name="Testing basics")
        db.add_all([section_1, section_2])
        db.flush()

        db.add_all([
            models.Lesson(id=1, section_id=1, name="HTTP methods and status codes", content_type="video"),
            models.Lesson(id=2, section_id=1, name="Request and response validation", content_type="text"),
            models.Lesson(id=3, section_id=2, name="Bug report structure", content_type="text"),
            models.Lesson(id=4, section_id=2, name="Test design techniques", content_type="video"),
        ])

    db.commit()
