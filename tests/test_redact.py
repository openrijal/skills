"""Redaction and extraction tests. Run: python3 -m unittest discover -s tests -v

The fixture holds FAKE secrets, each with a '<<>>' marker spliced in after its
prefix so no scannable key is committed. The tests strip the marker to rebuild
the real-looking value, check it is present, then check redaction removes it.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "daily-log", "scripts")
sys.path.insert(0, SCRIPTS)
import redact  # noqa: E402
import extract_sessions  # noqa: E402

MARK = "<<>>"


def load_fixture():
    with open(os.path.join(HERE, "fixtures", "seeded_transcript.jsonl"), encoding="utf-8") as fh:
        raw = fh.read().replace(MARK, "")
    with open(os.path.join(HERE, "fixtures", "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["secrets"] = [s.replace(MARK, "") for s in manifest["secrets"]]
    return raw, manifest


def deny_patterns(manifest):
    return redact.load_deny(type("A", (), {"deny": ["Project Falcon", r"re:acme-\d+"], "deny_file": None, "config_dir": None})())


class RedactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.manifest = load_fixture()
        cls.out, cls.counts = redact.redact(cls.raw, deny_patterns(cls.manifest))

    def test_fixture_really_contains_every_secret_before_redaction(self):
        for s in self.manifest["secrets"]:
            self.assertIn(s, self.raw, "fixture lost %r" % s)

    def test_no_seeded_secret_survives(self):
        survivors = [s for s in self.manifest["secrets"] if s in self.out]
        self.assertEqual(survivors, [])

    def test_each_secret_type_was_counted(self):
        for label in ("private-key", "jwt", "aws-access-key", "github-token", "anthropic-key", "openai-key",
                      "slack-token", "google-api-key", "stripe-key", "bearer-token", "url-password",
                      "secret-assignment", "high-entropy", "deny-list"):
            self.assertGreater(self.counts[label], 0, "no %s redactions" % label)

    def test_private_key_block_fully_masked(self):
        self.assertNotIn("BEGIN RSA PRIVATE KEY", self.out)
        self.assertNotIn("QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5", self.out)

    def test_truncated_private_key_masked(self):
        text = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSj\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nand then prose"
        out, _ = redact.redact(text)
        self.assertNotIn("MIIEvQIBADANBgkq", out)
        self.assertIn("and then prose", out)

    def test_safe_text_survives_unchanged(self):
        for line in self.manifest["keep"]:
            self.assertIn(line, self.out, "redactor damaged: %r" % line)

    def test_idempotent(self):
        again, _ = redact.redact(self.out, deny_patterns(self.manifest))
        self.assertEqual(again, self.out)

    def test_git_sha_alone_survives(self):
        sha = "3f786850e387550fdab836ed7e6dc881de23001b"
        out, _ = redact.redact("merged %s into main" % sha)
        self.assertIn(sha, out)

    def test_placeholders_are_not_masked(self):
        text = "password=${DB_PASSWORD} and token=<your-token-here> and api_key=changeme"
        out, _ = redact.redact(text)
        self.assertEqual(out, text)

    def test_cli_filters_stdin_and_check_mode(self):
        script = os.path.join(SCRIPTS, "redact.py")
        r = subprocess.run([sys.executable, script], input=self.raw.encode(), capture_output=True)
        self.assertEqual(r.returncode, 0)
        out = r.stdout.decode()
        self.assertEqual([s for s in self.manifest["secrets"] if s in out and s not in self.manifest["deny"]], [])
        c = subprocess.run([sys.executable, script, "--check"], input=self.raw.encode(), capture_output=True)
        self.assertEqual(c.returncode, 3)
        clean = subprocess.run([sys.executable, script, "--check"], input=b"Fixed the bug in PR 42.\n", capture_output=True)
        self.assertEqual(clean.returncode, 0)

    def test_cli_deny_file_from_config_dir(self):
        script = os.path.join(SCRIPTS, "redact.py")
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "deny.txt"), "w") as fh:
                fh.write("# comment\nBlue Heron\nre:cust-\\d{4}\n")
            r = subprocess.run([sys.executable, script, "--config-dir", d],
                               input=b"Blue Heron call about cust-1234 went well", capture_output=True)
            self.assertNotIn(b"Blue Heron", r.stdout)
            self.assertNotIn(b"cust-1234", r.stdout)
            self.assertIn(b"went well", r.stdout)


class ExtractTests(unittest.TestCase):
    def write(self, d, name, records):
        p = os.path.join(d, name)
        with open(p, "w") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
        return p

    def run_extract(self, agent, path):
        script = os.path.join(SCRIPTS, "extract_sessions.py")
        r = subprocess.run([sys.executable, script, agent, path, "--since", "2026-11-12T00:00:00-06:00",
                            "--until", "2026-11-13T00:00:00-06:00"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout, r.stderr

    def test_claude_keeps_only_conversation_text_in_window(self):
        with tempfile.TemporaryDirectory() as d:
            ts = "2026-11-12T20:00:00.000Z"
            p = self.write(d, "s.jsonl", [
                {"type": "api-request-shape", "timestamp": ts, "shape": {"system": [{"text": "SYSTEM PROMPT LEAK"}]}},
                {"type": "attachment", "timestamp": ts, "attachment": {"stdout": "HOOK OUTPUT"}},
                {"type": "user", "timestamp": ts, "cwd": "/x/proj", "message": {"role": "user", "content": "Add retry logic"}},
                {"type": "user", "timestamp": ts, "cwd": "/x/proj", "message": {"role": "user", "content": [{"type": "tool_result", "content": "TOOL OUT"}]}},
                {"type": "assistant", "timestamp": ts, "cwd": "/x/proj", "message": {"role": "assistant", "content": [
                    {"type": "thinking", "thinking": "HIDDEN REASONING"},
                    {"type": "tool_use", "name": "Bash", "input": {"command": "cat .env"}},
                    {"type": "text", "text": "Added retry with backoff."}]}},
                {"type": "user", "timestamp": "2026-11-10T20:00:00Z", "cwd": "/x/proj", "message": {"role": "user", "content": "too old"}},
                {"type": "user", "timestamp": ts, "cwd": "/x/proj", "message": {"role": "user", "content": "<system-reminder>injected</system-reminder>"}},
            ])
            out, err = self.run_extract("claude", p)
            self.assertIn("Add retry logic", out)
            self.assertIn("Added retry with backoff.", out)
            for bad in ("SYSTEM PROMPT LEAK", "HOOK OUTPUT", "TOOL OUT", "HIDDEN REASONING", "cat .env", "too old", "injected"):
                self.assertNotIn(bad, out)
            self.assertIn("2 message(s) kept", err)

    def test_codex_drops_developer_messages(self):
        with tempfile.TemporaryDirectory() as d:
            ts = "2026-11-12T21:00:00.000Z"
            mk = lambda role, typ, text: {"type": "response_item", "timestamp": ts, "payload": {
                "type": "message", "role": role, "content": [{"type": typ, "text": text}]}}
            p = self.write(d, "rollout.jsonl", [
                mk("developer", "input_text", "DEVELOPER INSTRUCTIONS"),
                mk("user", "input_text", "Write the migration"),
                mk("assistant", "output_text", "Migration written."),
                {"type": "response_item", "timestamp": ts, "payload": {"type": "custom_tool_call", "name": "shell", "input": "env"}},
                {"type": "event_msg", "timestamp": ts, "payload": {"type": "token_count"}},
            ])
            out, err = self.run_extract("codex", p)
            self.assertIn("Write the migration", out)
            self.assertIn("Migration written.", out)
            self.assertNotIn("DEVELOPER INSTRUCTIONS", out)
            self.assertIn("2 message(s) kept", err)

    def test_empty_window_reports_zero_so_the_runner_can_say_so(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.write(d, "s.jsonl", [])
            _, err = self.run_extract("claude", p)
            self.assertIn("0 message(s) kept", err)


if __name__ == "__main__":
    unittest.main()
