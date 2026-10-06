import unittest

from tests.helpers import ADA, BO, DEE, TEAM, call, make_env

SCREEN = f"/settings/teams/{TEAM}"


class TeamScreenTest(unittest.TestCase):
    def setUp(self):
        self.conn, self.app = make_env()

    def test_admin_sees_controls(self):
        status, html = call(self.app, "GET", SCREEN, user_id=ADA)
        self.assertEqual(status, 200)
        self.assertIn("3 members", html)
        self.assertIn('class="js-role"', html)
        self.assertIn("team_members.js", html)

    def test_member_sees_a_read_only_list(self):
        status, html = call(self.app, "GET", SCREEN, user_id=BO)
        self.assertEqual(status, 200)
        self.assertIn("Bo", html)
        self.assertNotIn('class="js-role"', html)
        self.assertNotIn("team_members.js", html)

    def test_outsider_gets_not_found(self):
        status, _ = call(self.app, "GET", SCREEN, user_id=DEE)
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
