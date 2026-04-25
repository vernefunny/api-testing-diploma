# Schemathesis CLI fixed patch

## Что исправлено

Старый патч пытался запускать:

```text
python -m schemathesis
```

Но в установленной версии Schemathesis так нельзя, потому что у пакета нет `__main__.py`.

Новый файл ищет настоящий CLI:

```text
.venv\Scripts\schemathesis.exe
```

и запускает уже его.

## Что сделать

1. Замени файл:

```text
E:\edu_api_test_framework\tests\contracts\test_schemathesis_contract.py
```

на файл из этого архива.

2. Удали временный тест, который мы создавали для проверки Allure:

```powershell
Remove-Item tests\test_allure_check.py
```

3. Запусти:

```powershell
Remove-Item -Recurse -Force allure-results
pytest --alluredir=allure-results --clean-alluredir
allure serve allure-results
```
