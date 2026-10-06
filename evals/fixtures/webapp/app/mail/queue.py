"""Outgoing mail queue.

Messages are stored first and delivered later by a worker, so a slow or failing
mail provider never blocks a request.
"""

MAX_ATTEMPTS = 3


def enqueue(conn, to_email, subject, body):
    cursor = conn.execute(
        "INSERT INTO mail_queue (to_email, subject, body) VALUES (?, ?, ?)",
        (to_email, subject, body),
    )
    conn.commit()
    return cursor.lastrowid


def pending(conn, limit=20):
    rows = conn.execute(
        "SELECT * FROM mail_queue WHERE status = 'pending' ORDER BY id LIMIT ?", (limit,)
    )
    return [dict(row) for row in rows]


def deliver_pending(conn, transport, limit=20):
    """Send pending messages and return how many went out.

    ``transport(to_email, subject, body)`` sends one message and raises on
    failure. A message that fails ``MAX_ATTEMPTS`` times is marked failed and
    left for a person to look at.
    """
    sent = 0
    for message in pending(conn, limit):
        try:
            transport(message["to_email"], message["subject"], message["body"])
        except Exception as exc:  # the transport decides what can go wrong
            attempts = message["attempts"] + 1
            status = "failed" if attempts >= MAX_ATTEMPTS else "pending"
            conn.execute(
                "UPDATE mail_queue SET attempts = ?, status = ?, last_error = ? WHERE id = ?",
                (attempts, status, str(exc), message["id"]),
            )
        else:
            conn.execute(
                "UPDATE mail_queue SET status = 'sent', sent_at = datetime('now'),"
                " attempts = attempts + 1 WHERE id = ?",
                (message["id"],),
            )
            sent += 1
        conn.commit()
    return sent
