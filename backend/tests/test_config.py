"""配置与启动期自检测试（对应 docs/tech/14-评估与改进.md P0-2 / P1-8）。"""

from datetime import datetime, timezone

import pytest

from app.core import config as config_module
from app.core.config import (
    business_day_start,
    business_day_start_utc_naive,
    describe_effective_config,
    insecure_defaults,
    to_utc_naive,
)


# ─────────────────── 占位密钥检测（P0-2） ───────────────────


def test_insecure_defaults_detects_placeholders(monkeypatch):
    monkeypatch.setattr(config_module.settings, "SECRET_KEY", "your-secret-key-change-in-production")
    monkeypatch.setattr(config_module.settings, "API_KEY", "dev-api-key-change-in-production")
    assert insecure_defaults() == ["SECRET_KEY", "API_KEY"]


def test_insecure_defaults_empty_for_strong_values(monkeypatch):
    monkeypatch.setattr(config_module.settings, "SECRET_KEY", "a7f3" * 8)
    monkeypatch.setattr(config_module.settings, "API_KEY", "b19e" * 8)
    assert insecure_defaults() == []


def test_assert_secure_config_refuses_to_start_in_production(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(config_module.settings, "SECRET_KEY", "change-me-to-a-random-secret")
    with pytest.raises(RuntimeError):
        config_module.assert_secure_config()


def test_assert_secure_config_only_warns_in_development(monkeypatch, caplog):
    monkeypatch.setattr(config_module.settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(config_module.settings, "API_KEY", "dev-api-key-change-in-production")

    config_module.assert_secure_config()  # 不应抛异常

    assert any("占位值" in rec.message for rec in caplog.records)


def test_assert_secure_config_passes_with_strong_secrets(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(config_module.settings, "SECRET_KEY", "c0ffee" * 4)
    monkeypatch.setattr(config_module.settings, "API_KEY", "deadbeef" * 3)
    config_module.assert_secure_config()  # 不应抛异常


# ─────────────── 有效配置摘要不得泄露凭据（P1-8） ───────────────


def test_describe_effective_config_masks_credentials(monkeypatch):
    monkeypatch.setattr(
        config_module.settings,
        "DATABASE_URL",
        "mysql+pymysql://user:supersecretpw@db-host:3306/campus_monitor",
    )
    monkeypatch.setattr(config_module.settings, "REDIS_URL", "redis://:redispw@cache:6379/0")
    monkeypatch.setattr(config_module.settings, "SECRET_KEY", "topsecretvalue")

    summary = describe_effective_config()

    assert "supersecretpw" not in summary
    assert "redispw" not in summary
    assert "topsecretvalue" not in summary
    assert "db-host:3306/campus_monitor" in summary


# ─────────────────── 业务时区换算（P1-8） ───────────────────


def test_business_day_start_uses_business_timezone(monkeypatch):
    monkeypatch.setattr(config_module.settings, "BUSINESS_TIMEZONE", "Asia/Shanghai")
    # UTC 2026-09-16 03:30 == 北京 11:30（同一天）
    start = business_day_start(datetime(2026, 9, 16, 3, 30, tzinfo=timezone.utc))

    assert (start.hour, start.minute, start.second) == (0, 0, 0)
    assert start.strftime("%Y-%m-%d") == "2026-09-16"
    # 北京 2026-09-16 00:00 == UTC 2026-09-15 16:00
    assert to_utc_naive(start) == datetime(2026, 9, 15, 16, 0)


def test_business_day_start_rolls_over_at_utc_16(monkeypatch):
    """UTC 16:00 之后已是北京次日，日界必须跟随业务时区而不是 UTC。"""
    monkeypatch.setattr(config_module.settings, "BUSINESS_TIMEZONE", "Asia/Shanghai")
    start = business_day_start_utc_naive(datetime(2026, 9, 16, 17, 0, tzinfo=timezone.utc))

    assert start == datetime(2026, 9, 16, 16, 0)
