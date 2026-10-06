import unittest

from app.mail import queue
from tests.helpers import call, make_env


class MailQueueTest(unittest.TestCase):
    def setUp(self):
        self.conn, self.app = make_env()

    def test_delivers_pending_messages(self):
        queue.enqueue(self.conn, "bo@example.com", "Hello", "Body")
        outbox = []
        sent = queue.deliver_pending(self.conn, lambda *message: outbox.append(message))
        self.assertEqual(sent, 1)
        self.assertEqual(outbox, [("bo@example.com", "Hello", "Body")])
        self.assertEqual(queue.pending(self.conn), [])

    def test_gives_up_after_max_attempts(self):
        queue.enqueue(self.conn, "bo@example.com", "Hello", "Body")

        def broken(*_message):
            raise RuntimeError("provider down")

        for _ in range(queue.MAX_ATTEMPTS):
            queue.deliver_pending(self.conn, broken)
        row = self.conn.execute("SELECT status, attempts, last_error FROM mail_queue").fetchone()
        self.assertEqual((row["status"], row["attempts"]), ("failed", queue.MAX_ATTEMPTS))
        self.assertEqual(row["last_error"], "provider down")


class PasswordResetMailTest(unittest.TestCase):
    def setUp(self):
        self.conn, self.app = make_env()

    def test_known_email_queues_a_reset_link(self):
        status, _ = call(self.app, "POST", "/api/password-resets", body={"email": "Bo@Example.com"})
        self.assertEqual(status, 202)
        (message,) = queue.pending(self.conn)
        self.assertEqual(message["to_email"], "bo@example.com")
        self.assertEqual(message["subject"], "Reset your Teamdesk password")
        self.assertIn("https://teamdesk.test/reset-password?token=", message["body"])

    def test_unknown_email_gets_the_same_answer_and_no_mail(self):
        status, _ = call(self.app, "POST", "/api/password-resets", body={"email": "nobody@example.com"})
        self.assertEqual(status, 202)
        self.assertEqual(queue.pending(self.conn), [])


if __name__ == "__main__":
    unittest.main()
