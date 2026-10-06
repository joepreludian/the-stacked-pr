import unittest

from tests.helpers import ADA, BO, CY, DEE, TEAM, call, make_env

MEMBERS = f"/api/teams/{TEAM}/members"


class ListMembersTest(unittest.TestCase):
    def setUp(self):
        self.conn, self.app = make_env()

    def test_any_member_can_list(self):
        status, body = call(self.app, "GET", MEMBERS, user_id=CY)
        self.assertEqual(status, 200)
        self.assertEqual([m["name"] for m in body["members"]], ["Ada", "Bo", "Cy"])

    def test_requires_sign_in(self):
        status, _ = call(self.app, "GET", MEMBERS)
        self.assertEqual(status, 401)

    def test_outsiders_cannot_tell_the_team_exists(self):
        status, _ = call(self.app, "GET", MEMBERS, user_id=DEE)
        self.assertEqual(status, 404)


class UpdateMemberTest(unittest.TestCase):
    def setUp(self):
        self.conn, self.app = make_env()

    def test_admin_changes_a_role(self):
        status, body = call(self.app, "PATCH", f"{MEMBERS}/2", user_id=ADA, body={"role": "admin"})
        self.assertEqual(status, 200)
        self.assertEqual(body["member"]["role"], "admin")

    def test_non_admin_is_forbidden(self):
        status, _ = call(self.app, "PATCH", f"{MEMBERS}/3", user_id=BO, body={"role": "member"})
        self.assertEqual(status, 403)

    def test_unknown_role_is_rejected(self):
        status, body = call(self.app, "PATCH", f"{MEMBERS}/2", user_id=ADA, body={"role": "owner"})
        self.assertEqual(status, 422)
        self.assertIn("role must be one of", body["error"])

    def test_last_admin_cannot_be_demoted(self):
        status, _ = call(self.app, "PATCH", f"{MEMBERS}/1", user_id=ADA, body={"role": "member"})
        self.assertEqual(status, 409)

    def test_invalid_json_is_a_bad_request(self):
        environ_body = "not json"
        status, _ = call(self.app, "PATCH", f"{MEMBERS}/2", user_id=ADA, body=environ_body)
        self.assertEqual(status, 400)


class RemoveMemberTest(unittest.TestCase):
    def setUp(self):
        self.conn, self.app = make_env()

    def test_admin_removes_a_member(self):
        status, _ = call(self.app, "DELETE", f"{MEMBERS}/2", user_id=ADA)
        self.assertEqual(status, 204)
        _, body = call(self.app, "GET", MEMBERS, user_id=ADA)
        self.assertEqual([m["name"] for m in body["members"]], ["Ada", "Cy"])

    def test_last_admin_cannot_be_removed(self):
        status, _ = call(self.app, "DELETE", f"{MEMBERS}/1", user_id=ADA)
        self.assertEqual(status, 409)

    def test_unknown_member_is_not_found(self):
        status, _ = call(self.app, "DELETE", f"{MEMBERS}/99", user_id=ADA)
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
