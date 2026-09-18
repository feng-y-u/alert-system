"""Bug 修复回归测试（BUG-001 / BUG-002 / BUG-003 / BUG-007 / BUG-008）。

对应审查报告中的 P0/P1/P2 缺陷，锁死修复后的行为，防止回退。
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.alert import Alert
from app.models.login_log import LoginLog
from app.models.user import User
from app.schemas.logs_query import LogQueryParams


def _admin_headers(db) -> dict:
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user.id)})}"}


def _add_log(db, username, login_time, status="success", ip="10.0.0.1"):
    log = LoginLog(
        username=username,
        login_time=login_time,
        ip_address=ip,
        user_agent="pytest",
        login_status=status,
    )
    db.add(log)
    db.commit()
    return log


# ─────────────── BUG-001：时区感知的查询参数 ───────────────


class TestLogQueryParamsTimezone:
    """带 offset 的入参必须归一化为 UTC naive，且不得漏成 500。"""

    def test_aware_and_naive_mixed_does_not_raise(self):
        """修复前：混合时区感知抛 TypeError 并穿透成 500。"""
        params = LogQueryParams(
            start_time="2026-09-16T00:00:00+08:00",
            end_time="2026-09-16T23:59:59",
        )
        assert params.start_time == datetime(2026, 9, 15, 16, 0)
        assert params.start_time.tzinfo is None
        assert params.end_time.tzinfo is None

    def test_both_aware_normalized_to_utc(self):
        params = LogQueryParams(
            start_time="2026-09-16T00:00:00+08:00",
            end_time="2026-09-16T23:59:59+08:00",
        )
        assert params.start_time == datetime(2026, 9, 15, 16, 0)
        assert params.end_time == datetime(2026, 9, 16, 15, 59, 59)

    def test_negative_offset_normalized(self):
        params = LogQueryParams(start_time="2026-09-16T00:00:00-05:00")
        assert params.start_time == datetime(2026, 9, 16, 5, 0)

    def test_naive_passes_through_unchanged(self):
        params = LogQueryParams(
            start_time="2026-09-16T00:00:00", end_time="2026-09-16T23:59:59"
        )
        assert params.start_time == datetime(2026, 9, 16, 0, 0)

    def test_reversed_range_rejected_with_422(self):
        """反序必须被拒绝，且是 HTTPException(422) 而不是 ValueError（后者会变 500）。"""
        with pytest.raises(HTTPException) as exc:
            LogQueryParams(
                start_time="2026-09-16T23:00:00+08:00",
                end_time="2026-09-16T01:00:00+08:00",
            )
        assert exc.value.status_code == 422

    def test_reversed_range_mixed_offset_rejected(self):
        with pytest.raises(HTTPException) as exc:
            LogQueryParams(
                start_time="2026-09-16T23:00:00+08:00",
                end_time="2026-09-16T01:00:00",
            )
        assert exc.value.status_code == 422


def test_list_logs_accepts_mixed_offset(client, db):
    """混合 offset 的查询参数返回 200（修复前 500）。"""
    headers = _admin_headers(db)
    for qs in (
        "start_time=2026-09-16T00:00:00%2B08:00&end_time=2026-09-16T23:59:59",
        "start_time=2026-09-16T00:00:00&end_time=2026-09-16T23:59:59%2B08:00",
        "start_time=2026-09-16T00:00:00%2B08:00&end_time=2026-09-16T23:59:59%2B08:00",
    ):
        assert client.get(f"/api/logs?{qs}", headers=headers).status_code == 200


def test_list_logs_reversed_range_returns_422(client, db):
    headers = _admin_headers(db)
    resp = client.get(
        "/api/logs?start_time=2026-09-17T00:00:00&end_time=2026-09-16T00:00:00",
        headers=headers,
    )
    assert resp.status_code == 422


class TestLogQueryParamConstraintsNotLeakingAs500:
    """/api/logs 的**所有**参数约束都必须返回 422，而不是 500。

    根因（BUG-001 的完整影响面）：``LogQueryParams`` 以 ``Depends()`` 注入，
    FastAPI 只对「请求体」与「单个 Query/Path 参数」把校验错误转成 422；
    以 ``Depends(<pydantic 模型>)`` 注入时 ``ValidationError`` 会穿透成 500。
    因此这里逐个约束都要锁死状态码。
    """

    @pytest.mark.parametrize(
        "query",
        [
            "limit=101",          # 上限
            "limit=0",            # 下限
            "limit=abc",          # 类型
            "skip=-1",            # 下限
            "skip=abc",           # 类型
            "login_status=bogus",  # pattern
        ],
    )
    def test_invalid_param_returns_422(self, client, db, query):
        headers = _admin_headers(db)
        resp = client.get(f"/api/logs?{query}", headers=headers)
        assert resp.status_code == 422, f"{query} 返回了 {resp.status_code}"

    @pytest.mark.parametrize(
        "query",
        [
            "limit=1",
            "limit=100",
            "skip=0",
            "skip=100000",
            "login_status=success",
            "login_status=failure",
            "limit=20&skip=0",
        ],
    )
    def test_valid_param_returns_200(self, client, db, query):
        headers = _admin_headers(db)
        resp = client.get(f"/api/logs?{query}", headers=headers)
        assert resp.status_code == 200, f"{query} 返回了 {resp.status_code}"

    def test_missing_optional_params_use_defaults(self, client, db):
        """不带任何参数时按默认值工作（skip=0 / limit=50）。"""
        headers = _admin_headers(db)
        resp = client.get("/api/logs", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["skip"] == 0
        assert resp.json()["limit"] == 50


# ─────────────── BUG-003：日期筛选按业务时区折算 ───────────────


class TestLogDateFilterBusinessTimezone:
    """界面上的日期范围是自然日，必须按 BUSINESS_TIMEZONE 折算后再查库。

    默认 Asia/Shanghai：北京时间 2026-09-16 全天
    = UTC 2026-09-15T16:00 ~ 2026-09-16T16:00。
    """

    @pytest.fixture
    def seeded(self, db):
        # 北京 09-16 04:00（在范围内）
        _add_log(db, "stu", datetime(2026, 9, 15, 20, 0))
        # 北京 09-16 09:30（在范围内）
        _add_log(db, "stu", datetime(2026, 9, 16, 1, 30))
        # 北京 09-17 04:00（不在范围内）
        _add_log(db, "stu", datetime(2026, 9, 16, 20, 0))
        return db

    def test_shanghai_day_boundaries(self, client, seeded):
        headers = _admin_headers(seeded)
        resp = client.get(
            "/api/logs?start_time=2026-09-16T00:00:00&end_time=2026-09-16T23:59:59",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        # 修复前会把 UTC 09-16T20:00（北京 09-17）也算进来
        assert sorted(i["login_time"] for i in data["items"]) == [
            "2026-09-15T20:00:00",
            "2026-09-16T01:30:00",
        ]

    def test_next_day_excludes_previous(self, client, seeded):
        headers = _admin_headers(seeded)
        resp = client.get(
            "/api/logs?start_time=2026-09-17T00:00:00&end_time=2026-09-17T23:59:59",
            headers=headers,
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["login_time"] == "2026-09-16T20:00:00"

    def test_explicit_offset_gives_same_result(self, client, seeded):
        """带 +08:00 的等价查询必须与裸本地时间结果一致。"""
        headers = _admin_headers(seeded)
        bare = client.get(
            "/api/logs?start_time=2026-09-16T00:00:00&end_time=2026-09-16T23:59:59",
            headers=headers,
        ).json()
        offset = client.get(
            "/api/logs?start_time=2026-09-16T00:00:00%2B08:00"
            "&end_time=2026-09-16T23:59:59%2B08:00",
            headers=headers,
        ).json()
        assert bare["total"] == offset["total"] == 2


# ─────────────── BUG-007：LIKE 通配符转义 ───────────────


class TestUsernameFilterEscaping:
    """用户名筛选必须把 % 和 _ 当字面量，而不是 SQL 通配符。"""

    @pytest.fixture
    def seeded(self, db):
        for name in ("alice", "bob", "carol"):
            _add_log(db, name, datetime(2026, 9, 16, 1, 0))
        return db

    def test_underscore_is_literal(self, client, seeded):
        headers = _admin_headers(seeded)
        resp = client.get("/api/logs?username=_", headers=headers)
        # 修复前：_ 是单字符通配符，返回全部 3 条
        assert resp.json()["total"] == 0

    def test_percent_is_literal(self, client, seeded):
        headers = _admin_headers(seeded)
        resp = client.get("/api/logs?username=%25", headers=headers)
        # 修复前：% 匹配任意串，返回全部 3 条
        assert resp.json()["total"] == 0

    def test_partial_match_still_works(self, client, seeded):
        headers = _admin_headers(seeded)
        assert client.get("/api/logs?username=ali", headers=headers).json()["total"] == 1

    def test_exact_match_still_works(self, client, seeded):
        headers = _admin_headers(seeded)
        assert client.get("/api/logs?username=bob", headers=headers).json()["total"] == 1


# ─────────────── BUG-008：login_time 范围校验 ───────────────


class TestLoginTimeValidation:
    """login_time 必须归一化为 UTC naive，且拒绝明显超前的未来时间。"""

    def _post(self, client, login_time, username="stu08"):
        return client.post(
            "/api/logs",
            json={
                "username": username,
                "login_time": login_time,
                "ip_address": "10.0.0.1",
                "user_agent": "pytest",
                "login_status": "success",
            },
            headers={"X-API-Key": settings.API_KEY},
        )

    def test_current_time_accepted(self, client, db):
        now = datetime.now(timezone.utc)
        assert self._post(client, now.isoformat()).status_code == 201

    def test_small_clock_skew_tolerated(self, client, db):
        t = datetime.now(timezone.utc) + timedelta(minutes=2)
        assert self._post(client, t.isoformat()).status_code == 201

    def test_far_future_rejected(self, client, db):
        t = datetime.now(timezone.utc) + timedelta(minutes=10)
        assert self._post(client, t.isoformat()).status_code == 422

    def test_days_future_rejected(self, client, db):
        t = datetime.now(timezone.utc) + timedelta(days=3)
        assert self._post(client, t.isoformat()).status_code == 422

    def test_backfill_past_log_accepted(self, client, db):
        t = datetime.now(timezone.utc) - timedelta(hours=6)
        assert self._post(client, t.isoformat()).status_code == 201

    def test_offset_input_stored_as_utc_naive(self, client, db):
        """+08:00 入参必须折算为 UTC 后落库，而不是写入 +08:00 的墙钟时间。

        MySQL 对 aware datetime 会静默剥离 tzinfo，不归一化会差 8 小时。
        """
        base_utc = datetime.now(timezone.utc) - timedelta(hours=1)
        aware = base_utc.astimezone(timezone(timedelta(hours=8)))

        resp = self._post(client, aware.isoformat(), username="stu_offset")
        assert resp.status_code == 201

        stored = (
            db.query(LoginLog).filter(LoginLog.username == "stu_offset").one().login_time
        )
        assert stored.tzinfo is None
        delta = abs((stored - base_utc.replace(tzinfo=None)).total_seconds())
        assert delta < 2, f"落库时间与 UTC 相差 {delta} 秒（未归一化时应约 8 小时）"
