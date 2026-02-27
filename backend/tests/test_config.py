import os
import pytest

def test_jwt_secret_key_setting():
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-chars-minimum!!"
    from importlib import reload
    import config
    reload(config)
    assert config.settings.JWT_SECRET_KEY == "test-secret-key-32-chars-minimum!!"

def test_password_hash_setting():
    os.environ["SPARK_COACH_PASSWORD_HASH"] = "$2b$12$testhash"
    from importlib import reload
    import config
    reload(config)
    assert config.settings.SPARK_COACH_PASSWORD_HASH == "$2b$12$testhash"
