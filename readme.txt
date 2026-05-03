1. В отдельном powershell запускаем локально апи:

cd E:\api-testing-diploma\edu_api_demo_v3_sqlite
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

Проверка в браузере:
http://127.0.0.1:8000/docs

2. Далее запускаем фреймворк

cd E:\api-testing-diploma\edu_api_test_framework
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Remove-Item -Recurse -Force allure-results
pytest --alluredir=allure-results --clean-alluredir

3. Открыть отчет allure:

allure serve allure-results

4. Запуск без Schemathesis:

pytest --ignore=tests/contracts --alluredir=allure-results --clean-alluredir