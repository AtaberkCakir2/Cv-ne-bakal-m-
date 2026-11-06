from app.services.email import OUTBOX_LIMIT, EmailMessage, OutboxEmailSender


def message(number: int) -> EmailMessage:
    return EmailMessage(to="a@example.com", subject="Konu", body="Metin", link=f"https://x.test/?token={number}")


def test_outbox_keeps_only_the_latest_messages() -> None:
    sender = OutboxEmailSender()
    for number in range(OUTBOX_LIMIT + 5):
        sender.send(message(number))
    assert len(sender.outbox) == OUTBOX_LIMIT
    assert sender.outbox[0] == message(5)
    assert sender.outbox[-1] == message(OUTBOX_LIMIT + 4)
