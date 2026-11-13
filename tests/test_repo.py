"""Repo checks: skill frontmatter follows the Agent Skills spec, discovery is clean, copies match."""
import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILLS = os.path.join(ROOT, "skills")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    assert text.startswith("---\n"), "%s: frontmatter must start on line 1" % path
    end = text.index("\n---\n", 4)
    return text[4:end], text[end + 5:]


class SkillSpecTests(unittest.TestCase):
    def skill_dirs(self):
        return sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))

    def test_expected_skills_exist(self):
        self.assertEqual(self.skill_dirs(), ["daily-log", "daily-log-setup", "wiki-synthesis"])

    def test_frontmatter_follows_spec(self):
        for d in self.skill_dirs():
            fm, body = frontmatter(os.path.join(SKILLS, d, "SKILL.md"))
            name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M).group(1)
            self.assertEqual(name, d, "name must match the folder")
            self.assertLessEqual(len(name), 64)
            self.assertRegex(name, NAME_RE)
            m = re.search(r"^description:\s*>-?\n((?:  .*\n?)+)|^description:\s*(.+)$", fm, re.M)
            desc = " ".join((m.group(1) or m.group(2)).split())
            self.assertTrue(0 < len(desc) <= 1024, "description length %d" % len(desc))
            comp = re.search(r"^compatibility:\s*(.+)$", fm, re.M)
            if comp:
                self.assertLessEqual(len(comp.group(1)), 500)
            self.assertLess(len(body.splitlines()), 500)

    def test_only_three_skill_md_files_in_repo(self):
        found = []
        for dirpath, dirs, files in os.walk(ROOT):
            dirs[:] = [x for x in dirs if x != ".git"]
            if "SKILL.md" in files:
                found.append(os.path.relpath(dirpath, ROOT))
        self.assertEqual(sorted(found), ["skills/daily-log", "skills/daily-log-setup", "skills/wiki-synthesis"])

    def test_redact_copies_are_identical(self):
        a = open(os.path.join(SKILLS, "daily-log/scripts/redact.py"), "rb").read()
        b = open(os.path.join(SKILLS, "wiki-synthesis/scripts/redact.py"), "rb").read()
        self.assertEqual(a, b)

    def test_no_em_dashes_in_prose(self):
        bad = []
        for dirpath, dirs, files in os.walk(ROOT):
            dirs[:] = [x for x in dirs if x != ".git"]
            for f in files:
                if f.endswith((".md", ".yaml", ".txt", ".py")):
                    p = os.path.join(dirpath, f)
                    if "\u2014" in open(p, encoding="utf-8").read():
                        bad.append(os.path.relpath(p, ROOT))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
