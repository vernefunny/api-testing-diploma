from faker import Faker

fake = Faker()


def unique_email(prefix: str = "student") -> str:
    return f"{prefix}_{fake.uuid4()}@example.com"


def valid_register_payload(email: str | None = None) -> dict:
    return {
        "email": email or unique_email(),
        "password": "Password1!",
        "password_confirmation": "Password1!",
        "full_name": "Alexander Petrov",
        "birth_date": "2000-09-30",
        "receive_marketing_messages": False,
    }


def valid_login_payload(email: str, password: str = "Password1!") -> dict:
    return {
        "email": email,
        "password": password,
    }


def valid_profile_payload() -> dict:
    return {
        "full_name": "Alexander Updated",
        "birth_date": "1998-09-30",
        "receive_marketing_messages": True,
    }
