import pytest
from AppConfig import AppConfig  # Adjust the import path according to your project structure


def pytest_configure(config):
    app_config = AppConfig()

    if app_config.getIsProductionEnvironment():
        pytest.exit("Production environment is set. Skipping tests.")
