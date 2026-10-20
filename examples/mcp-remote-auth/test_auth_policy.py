import unittest

from auth_policy import authorize_http, stdio_child_env


class RemoteAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "iss": "https://login.example.com",
            "aud": "https://mcp.example.com/agent",
            "exp": 1_800_000_100,
            "sub": "user-17",
            "scope": "orders:read profile:read",
        }

    def decide(self, claims):
        return authorize_http(
            claims,
            expected_issuer="https://login.example.com",
            expected_audience="https://mcp.example.com/agent",
            required_scopes={"orders:read"},
            now=1_800_000_000,
        )

    def test_missing_token_is_401(self):
        self.assertEqual(self.decide(None).status, 401)

    def test_wrong_audience_is_401_even_when_user_matches(self):
        token = {**self.expected, "aud": "https://api.example.com"}
        decision = self.decide(token)
        self.assertEqual((decision.status, decision.reason), (401, "invalid_audience"))

    def test_wrong_issuer_is_401(self):
        decision = self.decide({**self.expected, "iss": "https://attacker.example"})
        self.assertEqual((decision.status, decision.reason), (401, "invalid_issuer"))

    def test_expired_token_is_401(self):
        decision = self.decide({**self.expected, "exp": 1_799_999_999})
        self.assertEqual((decision.status, decision.reason), (401, "expired_or_missing_expiry"))

    def test_missing_scope_is_403_after_authentication(self):
        decision = self.decide({**self.expected, "scope": "profile:read"})
        self.assertEqual((decision.status, decision.reason, decision.subject),
                         (403, "insufficient_scope", "user-17"))

    def test_valid_issuer_audience_expiry_and_scope_is_allowed(self):
        decision = self.decide(self.expected)
        self.assertEqual((decision.status, decision.subject), (200, "user-17"))

    def test_stdio_child_receives_only_allowlisted_secrets(self):
        env = {
            "MCP_API_TOKEN": "synthetic-token",
            "OPENAI_API_KEY": "unrelated-secret",
            "PATH": "/usr/bin",
        }
        child = stdio_child_env(env, {"MCP_API_TOKEN"})
        self.assertEqual(child, {"MCP_API_TOKEN": "synthetic-token"})


if __name__ == "__main__":
    unittest.main()
