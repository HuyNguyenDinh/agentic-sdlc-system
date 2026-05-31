import unittest

from src.bootstrap_gitnexus import (
    build_analyze_command,
    build_gitnexus_install_command,
    normalize_repo_input,
)


class TestBootstrapGitNexus(unittest.TestCase):
    def test_normalize_repo_input_accepts_slug(self):
        self.assertEqual(normalize_repo_input("org/repo"), "org/repo")

    def test_normalize_repo_input_accepts_https_url(self):
        self.assertEqual(
            normalize_repo_input("https://github.com/org/repo.git"),
            "org/repo",
        )

    def test_normalize_repo_input_accepts_ssh_url(self):
        self.assertEqual(
            normalize_repo_input("git@github.com:org/repo.git"),
            "org/repo",
        )

    def test_build_gitnexus_install_command(self):
        self.assertEqual(build_gitnexus_install_command(), ["npm", "install", "-g", "gitnexus"])

    def test_build_analyze_command_single_repo(self):
        self.assertEqual(build_analyze_command("org/repo"), ["npx", "gitnexus", "analyze", "org/repo"])


if __name__ == "__main__":
    unittest.main()