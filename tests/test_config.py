import json
import pytest
from cronwrap.config import Config


def test_default_values():
    cfg = Config(command="echo hello")
    assert cfg.timeout == 3600
    assert cfg.retries == 0
    assert cfg.retry_delay == 5
    assert cfg.alert_on_failure is True
    assert cfg.alert_on_success is False
    assert cfg.env == {}


def test_from_dict_basic():
    data = {"command": "ls -la", "timeout": 60, "retries": 2}
    cfg = Config.from_dict(data)
    assert cfg.command == "ls -la"
    assert cfg.timeout == 60
    assert cfg.retries == 2


def test_from_dict_ignores_unknown_keys():
    data = {"command": "echo", "unknown_key": "value"}
    cfg = Config.from_dict(data)
    assert cfg.command == "echo"


def test_from_file(tmp_path):
    config_data = {"command": "backup.sh", "timeout": 120, "alert_email": "admin@example.com"}
    config_file = tmp_path / "job.json"
    config_file.write_text(json.dumps(config_data))

    cfg = Config.from_file(str(config_file))
    assert cfg.command == "backup.sh"
    assert cfg.timeout == 120
    assert cfg.alert_email == "admin@example.com"


def test_from_file_not_found():
    with pytest.raises(FileNotFoundError):
        Config.from_file("/nonexistent/path/config.json")


def test_from_file_invalid_json(tmp_path):
    config_file = tmp_path / "bad.json"
    config_file.write_text("not valid json {{{")

    with pytest.raises(json.JSONDecodeError):
        Config.from_file(str(config_file))


def test_validate_passes():
    cfg = Config(command="echo ok")
    cfg.validate()  # should not raise


def test_validate_empty_command():
    cfg = Config(command="   ")
    with pytest.raises(ValueError, match="command"):
        cfg.validate()


def test_validate_negative_timeout():
    cfg = Config(command="echo", timeout=-1)
    with pytest.raises(ValueError, match="timeout"):
        cfg.validate()


def test_validate_negative_retries():
    cfg = Config(command="echo", retries=-1)
    with pytest.raises(ValueError, match="retries"):
        cfg.validate()


def test_to_dict_roundtrip():
    cfg = Config(command="echo", retries=3, alert_email="x@y.com")
    d = cfg.to_dict()
    cfg2 = Config.from_dict(d)
    assert cfg == cfg2
