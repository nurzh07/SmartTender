from app.tasks import email_tasks


def test_deliver_email_reports_reason_when_smtp_fails(monkeypatch):
    monkeypatch.setattr(email_tasks, "_send_smtp", lambda *args, **kwargs: False)
    monkeypatch.setattr(email_tasks, "_log_email_to_file", lambda *args, **kwargs: None)

    result = email_tasks._deliver_email(
        "user@example.com",
        "Test subject",
        "Test body",
    )

    assert result["status"] == "logged"
    assert result["email"] == "user@example.com"
    assert "reason" in result
