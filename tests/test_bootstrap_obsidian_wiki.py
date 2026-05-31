import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, mock_open
from src.bootstrap_obsidian_wiki import (
    DEFAULT_VAULT_PATH,
    normalize_repo_identifier,
    build_cron_line,
    merge_crontab,
    upsert_export_line,
    run_post_bootstrap_check,
    _install_obsidian_wiki,
)


class TestBootstrapObsidianWiki(unittest.TestCase):
    def test_normalize_repo_identifier_accepts_slug(self):
        self.assertEqual(normalize_repo_identifier("org/private-kb"), "org/private-kb")

    def test_normalize_repo_identifier_accepts_https(self):
        self.assertEqual(
            normalize_repo_identifier("https://github.com/org/private-kb.git"),
            "org/private-kb",
        )

    def test_normalize_repo_identifier_accepts_ssh(self):
        self.assertEqual(
            normalize_repo_identifier("git@github.com:org/private-kb.git"),
            "org/private-kb",
        )

    def test_normalize_repo_identifier_rejects_invalid(self):
        with self.assertRaises(ValueError):
            normalize_repo_identifier("not-a-repo")

    def test_build_cron_line_uses_five_minute_schedule(self):
        line = build_cron_line(DEFAULT_VAULT_PATH, "main")
        self.assertTrue(line.startswith("*/5 * * * * "))
        self.assertIn('git commit -m "automated backup commit"', line)
        self.assertIn("git push origin main", line)

    def test_merge_crontab_deduplicates_managed_line(self):
        managed = build_cron_line(DEFAULT_VAULT_PATH, "main")
        existing = managed + "\n"
        merged = merge_crontab(existing, managed)
        self.assertEqual(merged.count(managed), 1)

    def test_upsert_export_line_replaces_existing(self):
        content = 'export OBSIDIAN_VAULT_PATH="/tmp/old"\nexport OTHER="1"\n'
        updated = upsert_export_line(content, "OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH)
        self.assertIn(f'export OBSIDIAN_VAULT_PATH="{DEFAULT_VAULT_PATH}"', updated)
        self.assertIn('export OTHER="1"', updated)
        self.assertNotIn('export OBSIDIAN_VAULT_PATH="/tmp/old"', updated)

    @patch("src.bootstrap_obsidian_wiki.shutil.rmtree")
    @patch("src.bootstrap_obsidian_wiki._run")
    @patch("src.bootstrap_obsidian_wiki.tempfile.TemporaryDirectory")
    def test_install_obsidian_wiki_passes_vault_env_to_setup(self, mock_tmpdir, mock_run, mock_rmtree):
        mock_tmpdir.return_value.__enter__.return_value = "/tmp/install-root"
        mock_tmpdir.return_value.__exit__.return_value = False

        def _clone_side_effect(command, **kwargs):
            if command[:2] == ["git", "clone"]:
                Path(command[-1]).mkdir(parents=True, exist_ok=True)

        mock_run.side_effect = _clone_side_effect

        _install_obsidian_wiki(DEFAULT_VAULT_PATH)

        self.assertEqual(mock_run.call_count, 3)
        setup_call = mock_run.call_args_list[1]
        setup_cmd_call = mock_run.call_args_list[2]

        self.assertEqual(setup_call.args[0], ["env", f"OBSIDIAN_VAULT_PATH={DEFAULT_VAULT_PATH}", "bash", "setup.sh"])
        self.assertEqual(setup_call.kwargs["cwd"], "/tmp/install-root/obsidian-wiki")

        self.assertEqual(setup_cmd_call.args[0], ["obsidian-wiki", "setup", "--vault", DEFAULT_VAULT_PATH])
        self.assertEqual(setup_cmd_call.kwargs["env"]["OBSIDIAN_VAULT_PATH"], DEFAULT_VAULT_PATH)

        env_file = Path("/tmp/install-root/obsidian-wiki/.env")
        self.assertTrue(env_file.exists())
        self.assertIn(f'OBSIDIAN_VAULT_PATH="{DEFAULT_VAULT_PATH}"', env_file.read_text())
        mock_rmtree.assert_called_once_with(Path("/tmp/install-root/obsidian-wiki"), ignore_errors=True)

    @patch("src.bootstrap_obsidian_wiki._get_origin_repo_slug")
    @patch("src.bootstrap_obsidian_wiki._read_current_crontab")
    @patch("src.bootstrap_obsidian_wiki.Path.home")
    def test_post_bootstrap_check_succeeds(self, mock_home, mock_crontab, mock_origin):
        mock_home.return_value = Path("/tmp")
        profile_text = f'export OBSIDIAN_VAULT_PATH="{DEFAULT_VAULT_PATH}"\n'
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.read_text", return_value=profile_text):
            mock_crontab.return_value = build_cron_line(DEFAULT_VAULT_PATH, "main")
            mock_origin.return_value = "org/private-kb"
            args = SimpleNamespace(repo="org/private-kb", branch="main", vault_path=DEFAULT_VAULT_PATH)
            run_post_bootstrap_check(args)

    @patch("src.bootstrap_obsidian_wiki._get_origin_repo_slug")
    @patch("src.bootstrap_obsidian_wiki._read_current_crontab")
    @patch("src.bootstrap_obsidian_wiki.Path.home")
    def test_post_bootstrap_check_fails_when_cron_missing(self, mock_home, mock_crontab, mock_origin):
        mock_home.return_value = Path("/tmp")
        profile_text = f'export OBSIDIAN_VAULT_PATH="{DEFAULT_VAULT_PATH}"\n'
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.read_text", return_value=profile_text):
            mock_crontab.return_value = ""
            mock_origin.return_value = "org/private-kb"
            args = SimpleNamespace(repo="org/private-kb", branch="main", vault_path=DEFAULT_VAULT_PATH)
            with self.assertRaises(RuntimeError):
                run_post_bootstrap_check(args)


if __name__ == "__main__":
    unittest.main()
