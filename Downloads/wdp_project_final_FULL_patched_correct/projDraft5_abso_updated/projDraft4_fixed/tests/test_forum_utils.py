import run as app_run


def test_normalize_forum_category_defaults_to_life_skills():
    assert app_run._normalize_forum_category("Nope") == "Life Skills"
    assert app_run._normalize_forum_category("Money") == "Money"


def test_validate_forum_text_enforces_limits():
    title = "x" * (app_run.FORUM_TITLE_MAX + 1)
    content = "ok"
    assert "Title must be" in (app_run._validate_forum_text(title, content) or "")

    title = "ok"
    content = "x" * (app_run.FORUM_CONTENT_MAX + 1)
    assert "Content must be" in (app_run._validate_forum_text(title, content) or "")


def test_rate_limit_blocks_after_limit():
    key = "test-limit"
    app_run._RATE_LIMIT_BUCKETS.pop(key, None)

    ok, _ = app_run._rate_limit_check(key, limit=2, window_seconds=60)
    assert ok
    ok, _ = app_run._rate_limit_check(key, limit=2, window_seconds=60)
    assert ok
    ok, retry_after = app_run._rate_limit_check(key, limit=2, window_seconds=60)
    assert not ok
    assert retry_after >= 1


def test_forum_content_guard_flags_spam_and_offensive():
    assert app_run._forum_content_guard("you are stupid") is not None
    assert app_run._forum_content_guard("hellooooooo!!!!!!!!!!!!") is not None
    assert app_run._forum_content_guard("Friendly question about careers") is None
