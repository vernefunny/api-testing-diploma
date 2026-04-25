import os
import shutil
import subprocess
import uuid
from pathlib import Path

import allure
import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def create_token() -> str:
    """Create a fresh student and return JWT token for authenticated Schemathesis requests."""
    email = f"schemathesis_{uuid.uuid4()}@example.com"
    password = "Password1!"

    register_payload = {
        "email": email,
        "password": password,
        "password_confirmation": password,
        "full_name": "Schemathesis User",
        "birth_date": "2000-09-30",
        "receive_marketing_messages": False,
    }

    register_response = requests.post(
        f"{BASE_URL}/api/student/auth/register",
        json=register_payload,
        timeout=10,
    )
    assert register_response.status_code == 201, register_response.text

    login_response = requests.post(
        f"{BASE_URL}/api/student/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    assert login_response.status_code == 200, login_response.text

    return login_response.json()["access_token"]


def get_schemathesis_executable() -> str:
    """Find Schemathesis CLI in PATH or inside local virtual environment."""
    cli_from_path = shutil.which("schemathesis")
    if cli_from_path:
        return cli_from_path

    possible_windows_cli = Path.cwd() / ".venv" / "Scripts" / "schemathesis.exe"
    if possible_windows_cli.exists():
        return str(possible_windows_cli)

    possible_windows_bat = Path.cwd() / ".venv" / "Scripts" / "schemathesis.cmd"
    if possible_windows_bat.exists():
        return str(possible_windows_bat)

    possible_unix_cli = Path.cwd() / ".venv" / "bin" / "schemathesis"
    if possible_unix_cli.exists():
        return str(possible_unix_cli)

    raise AssertionError(
        "Schemathesis CLI executable was not found. "
        "Check that schemathesis is installed in the current venv."
    )


def run_schemathesis(command: list[str], token: str) -> subprocess.CompletedProcess[str]:
    """Run Schemathesis and attach command/output to Allure."""
    with allure.step("Run Schemathesis CLI"):
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )

    safe_command = " ".join(command).replace(token, "<TOKEN>")

    allure.attach(
        safe_command,
        name="Schemathesis command",
        attachment_type=allure.attachment_type.TEXT,
    )
    allure.attach(
        completed.stdout or "<empty stdout>",
        name="Schemathesis stdout",
        attachment_type=allure.attachment_type.TEXT,
    )
    allure.attach(
        completed.stderr or "<empty stderr>",
        name="Schemathesis stderr",
        attachment_type=allure.attachment_type.TEXT,
    )

    return completed


@allure.feature("Contract testing")
@allure.story("Read-only OpenAPI contract")
@pytest.mark.contract
def test_schemathesis_read_only_contract():
    """
    Stable Schemathesis check for read-only endpoints.

    Purpose:
    - test GET endpoints described in OpenAPI;
    - check that API does not return 5xx for generated path/query values;
    - keep this test stable for regular regression and CI/CD.
    """
    token = create_token()
    schemathesis_cli = get_schemathesis_executable()

    command = [
        schemathesis_cli,
        "run",
        f"{BASE_URL}/openapi.json",
        "--checks",
        "not_a_server_error",
        "--hypothesis-max-examples",
        "10",
        "--hypothesis-suppress-health-check",
        "filter_too_much,too_slow",
        "--header",
        f"Authorization: Bearer {token}",
        "--include-method",
        "GET",
        # These endpoints require previously created payment state and are tested by scenario pytest tests.
        "--exclude-path-regex",
        r"^/api/student/payments/.*",
        # Debug endpoints are not part of the student business API contract.
        "--exclude-path-regex",
        r"^/debug/.*",
    ]

    completed = run_schemathesis(command, token)

    assert completed.returncode == 0, (
        "Schemathesis found problems in read-only API contract. "
        "Open Allure attachment 'Schemathesis stdout' and check failed endpoint, "
        "test case ID and reproduction curl command."
    )


@allure.feature("Contract testing")
@allure.story("Robustness fuzzing")
@pytest.mark.contract
def test_schemathesis_robustness_no_server_errors():
    """
    Robustness check for mutable endpoints.

    Here 2xx and 4xx responses are acceptable:
    - 2xx means generated data happened to be valid;
    - 4xx means API correctly rejected invalid or unauthorized input;
    - 5xx is a defect because the server crashed instead of handling input safely.
    """
    token = create_token()
    schemathesis_cli = get_schemathesis_executable()

    command = [
        schemathesis_cli,
        "run",
        f"{BASE_URL}/openapi.json",
        "--checks",
        "not_a_server_error",
        "--hypothesis-max-examples",
        "10",
        "--hypothesis-suppress-health-check",
        "filter_too_much,too_slow",
        "--header",
        f"Authorization: Bearer {token}",
        # DELETE operations are excluded from fuzzing in the diploma project,
        # because they may change shared test data destructively.
        "--exclude-method",
        "DELETE",
        # Debug endpoints are not part of the student business API contract.
        "--exclude-path-regex",
        r"^/debug/.*",
    ]

    completed = run_schemathesis(command, token)

    assert completed.returncode == 0, (
        "Schemathesis found 5xx server errors during robustness testing. "
        "Open Allure attachment 'Schemathesis stdout' and check failed endpoint, "
        "test case ID and reproduction curl command."
    )
