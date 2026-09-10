"""Behavioral tests for project files, recovery and configuration contracts.

No test calls Codex, an LLM or the network. Temporary directories are disposable.
"""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cpo_installer", ROOT / "install.py")
cpo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cpo
spec.loader.exec_module(cpo)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "projeto com espaços e acentuação"
        self.project.mkdir()
        self.fake_home = self.base / "home"
        self.fake_home.mkdir()
        (self.fake_home / ".codex").mkdir()
        (self.fake_home / ".codex/config.toml").write_text('model = "global-sentinel"\n', encoding="utf-8")
        self.environment = patch.dict(os.environ, {"CODEX_HOME": str(self.fake_home / ".codex")})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.home = patch.object(Path, "home", return_value=self.fake_home)
        self.home.start()
        self.addCleanup(self.home.stop)

    def write(self, relative, content):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return path

    def tree(self, root=None):
        root = root or self.project
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def run_quiet(self, function, *args, **kwargs):
        with redirect_stdout(io.StringIO()):
            return function(*args, **kwargs)

    def install(self, **kwargs):
        return self.run_quiet(cpo.install, self.project, **kwargs)

    def uninstall(self, **kwargs):
        return self.run_quiet(cpo.uninstall, self.project, **kwargs)

    def test_fresh_install_is_project_scoped_and_uses_luna_max(self):
        global_before = self.tree(self.fake_home)
        self.install()
        config = tomllib.loads((self.project / cpo.CONFIG).read_text(encoding="utf-8"))
        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertEqual(config["model_reasoning_effort"], "low")
        self.assertEqual(config["agents"]["default_subagent_reasoning_effort"], "max")
        self.assertEqual(config["agents"]["max_concurrent_threads_per_session"], 2)
        self.assertEqual(self.tree(self.fake_home), global_before)
        for name, (model, effort) in cpo.ROLES.items():
            agent = tomllib.loads((self.project / f".codex/agents/{name}.toml").read_text(encoding="utf-8"))
            self.assertEqual((agent["model"], agent["model_reasoning_effort"]), (model, effort))
        self.assertIn(cpo.POLICY_BEGIN, (self.project / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual(self.run_quiet(cpo.status, self.project), 0)

    def test_dry_run_creates_no_files_or_directories(self):
        before = list(self.project.rglob("*"))
        self.install(dry_run=True)
        self.assertEqual(list(self.project.rglob("*")), before)

    def test_preserves_unrelated_toml_comments_tables_and_permissions(self):
        config = self.write(cpo.CONFIG, '# comentário preservado\nmodel = "old" # preferência anterior\n\n[sandbox_workspace_write]\nnetwork_access = false\n\n[mcp_servers."a.b"]\nurl = "https://example.test/mcp"\n\n[agents]\nmax_threads = 8\ninterrupt_message = false\n\n[agents.custom]\ndescription = "papel existente"\nconfig_file = "other.toml"\n')
        if os.name != "nt":
            config.chmod(0o600)
        before = self.tree()
        self.install()
        text = config.read_text(encoding="utf-8")
        data = tomllib.loads(text)
        self.assertIn("# comentário preservado", text)
        self.assertIn("# preferência anterior", text)
        self.assertFalse(data["sandbox_workspace_write"]["network_access"])
        self.assertEqual(data["mcp_servers"]["a.b"]["url"], "https://example.test/mcp")
        self.assertFalse(data["agents"]["interrupt_message"])
        self.assertEqual(data["agents"]["custom"]["config_file"], "other.toml")
        self.assertNotIn("max_threads", data["agents"])
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(config.stat().st_mode), 0o600)
        self.uninstall()
        self.assertEqual(self.tree(), before)

    def test_supports_inline_agents_table(self):
        self.write(cpo.CONFIG, 'agents = { enabled = false, interrupt_message = false }\n')
        self.install()
        result = tomllib.loads((self.project / cpo.CONFIG).read_text(encoding="utf-8"))
        self.assertTrue(result["agents"]["enabled"])
        self.assertFalse(result["agents"]["interrupt_message"])

    def test_prefers_nonempty_project_override_and_preserves_agents_md(self):
        self.write("AGENTS.md", "Instruções normais.\n")
        self.write("AGENTS.override.md", "Instruções prioritárias.\r\n")
        before = self.tree()
        self.install()
        self.assertEqual((self.project / "AGENTS.md").read_bytes(), before["AGENTS.md"])
        self.assertIn(cpo.POLICY_BEGIN.encode(), (self.project / "AGENTS.override.md").read_bytes())
        self.uninstall()
        self.assertEqual(self.tree(), before)

    def test_empty_override_does_not_hide_existing_instructions(self):
        self.write("AGENTS.override.md", b"")
        self.write("AGENTS.md", "Regras existentes.")
        self.install()
        state = cpo.load_state(self.project)
        self.assertEqual(state["instructions"], "AGENTS.md")
        self.assertEqual((self.project / "AGENTS.override.md").read_bytes(), b"")

    def test_repeated_install_is_idempotent(self):
        self.install()
        before = self.tree()
        mtimes = {p: p.stat().st_mtime_ns for p in self.project.rglob("*") if p.is_file()}
        self.install()
        self.assertEqual(self.tree(), before)
        self.assertEqual({p: p.stat().st_mtime_ns for p in mtimes}, mtimes)
        self.assertEqual((self.project / "AGENTS.md").read_text(encoding="utf-8").count(cpo.POLICY_BEGIN), 1)

    def test_mode_switch_keeps_original_backup_and_luna_max(self):
        self.write(cpo.CONFIG, 'model = "original"\n')
        before = self.tree()
        for mode, expected in cpo.MODES.items():
            self.install(mode=mode)
            data = tomllib.loads((self.project / cpo.CONFIG).read_text(encoding="utf-8"))
            self.assertEqual((data["model"], data["model_reasoning_effort"], data["agents"]["enabled"]), expected)
            self.assertEqual(data["agents"]["default_subagent_reasoning_effort"], "max")
        self.uninstall()
        self.assertEqual(self.tree(), before)

    def test_uninstall_fresh_install_restores_empty_project(self):
        self.install()
        self.uninstall()
        self.assertEqual(list(self.project.iterdir()), [])

    def test_uninstall_dry_run_preserves_everything(self):
        self.install()
        before = self.tree()
        self.uninstall(dry_run=True)
        self.assertEqual(self.tree(), before)

    def test_reinstall_and_uninstall_refuse_drift_without_touching_files(self):
        self.install()
        with (self.project / "AGENTS.md").open("a", encoding="utf-8") as stream:
            stream.write("\nUma nova regra do projeto.\n")
        before = self.tree()
        self.assertEqual(self.run_quiet(cpo.status, self.project), 2)
        with self.assertRaises(cpo.InstallError):
            self.install()
        with self.assertRaises(cpo.InstallError):
            self.uninstall()
        self.assertEqual(self.tree(), before)

    def test_status_detects_new_override(self):
        self.install()
        self.write("AGENTS.override.md", "Agora este arquivo tem precedência.")
        self.assertEqual(self.run_quiet(cpo.status, self.project), 2)
        with self.assertRaises(cpo.InstallError):
            self.install()

    def test_invalid_toml_does_not_leave_partial_install(self):
        self.write(cpo.CONFIG, 'model = [broken\n')
        before = self.tree()
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(), before)
        self.assertFalse((self.project / cpo.STATE_DIR).exists())

    def test_scalar_agents_is_rejected(self):
        self.write(cpo.CONFIG, 'agents = false\n')
        before = self.tree()
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(), before)

    def test_existing_role_filename_is_not_overwritten(self):
        self.write(".codex/agents/cpo_worker.toml", 'name = "mine"\n')
        before = self.tree()
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(), before)

    def test_existing_role_name_in_other_file_is_not_shadowed(self):
        self.write(".codex/agents/other.toml", 'name = "cpo_worker"\n')
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertFalse((self.project / cpo.CONFIG).exists())

    def test_legacy_role_name_collision_is_rejected(self):
        self.write(cpo.CONFIG, '[agents.cpo_worker]\nconfig_file = "mine.toml"\n')
        with self.assertRaises(cpo.InstallError):
            self.install()

    def test_invalid_existing_agent_name_reports_a_preflight_error(self):
        self.write(".codex/agents/other.toml", 'name = ["invalid"]\n')
        before = self.tree()
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(), before)

    def test_orphan_policy_marker_requires_manual_resolution(self):
        self.write("AGENTS.md", cpo.POLICY_BEGIN + "\nLocal content\n" + cpo.POLICY_END)
        before = self.tree()
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(), before)

    def test_file_in_place_of_codex_directory_is_rejected(self):
        self.write(".codex", b"ordinary file")
        with self.assertRaises(cpo.InstallError):
            self.install()

    def test_rejects_home_and_codex_home_targets(self):
        for path in (self.fake_home, self.fake_home / ".codex", Path(self.project.anchor)):
            with self.subTest(path=path), self.assertRaises(cpo.InstallError):
                self.run_quiet(cpo.install, path)

    def test_explicit_project_is_required_by_cli(self):
        result = subprocess.run([sys.executable, str(ROOT / "install.py"), "install"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--project", result.stderr)

    def test_symlink_cannot_redirect_project_configuration(self):
        destination = self.fake_home / ".codex"
        try:
            (self.project / ".codex").symlink_to(destination, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink permission is unavailable on this runner.")
        before = self.tree(self.fake_home)
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(self.fake_home), before)

    def test_hardlink_cannot_redirect_configuration(self):
        (self.project / ".codex").mkdir()
        try:
            os.link(self.fake_home / ".codex/config.toml", self.project / cpo.CONFIG)
        except (OSError, NotImplementedError):
            self.skipTest("Hard links unavailable.")
        before = self.tree(self.fake_home)
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(self.fake_home), before)

    def test_reparse_point_is_rejected_without_path_is_junction(self):
        reparse = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        with patch.object(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400, create=True):
            with patch.object(Path, "lstat", return_value=reparse), patch.object(Path, "is_junction", return_value=False, create=True):
                with self.assertRaises(cpo.InstallError):
                    cpo.local_path(self.project, ".codex")

    @unittest.skipUnless(os.name == "nt", "Native Windows junction test.")
    def test_windows_junction_cannot_redirect_configuration(self):
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(self.project / ".codex"), str(self.fake_home / ".codex")],
            capture_output=True,
        )
        if result.returncode:
            self.skipTest("Junction creation unavailable on this runner.")
        before = self.tree(self.fake_home)
        try:
            with self.assertRaises(cpo.InstallError):
                self.install()
            self.assertEqual(self.tree(self.fake_home), before)
        finally:
            (self.project / ".codex").rmdir()

    def test_tampered_manifest_cannot_restore_outside_project(self):
        self.install()
        state_file = self.project / cpo.STATE_FILE
        state = json.loads(state_file.read_text())
        state["files"]["../../outside"] = state["files"].pop("AGENTS.md")
        state_file.write_text(json.dumps(state), encoding="utf-8")
        before = self.tree()
        with self.assertRaises(cpo.InstallError):
            self.uninstall()
        self.assertEqual(self.tree(), before)

    def test_corrupted_backup_is_rejected(self):
        self.write("AGENTS.md", "original")
        self.install()
        self.write(cpo.original_path("AGENTS.md"), "corrupted")
        with self.assertRaises(cpo.InstallError):
            self.uninstall()
        self.assertTrue((self.project / cpo.CONFIG).exists())

    def test_lock_prevents_concurrent_operations(self):
        self.write(cpo.LOCK_FILE, "12345")
        before = self.tree()
        with self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual(self.tree(), before)

    def test_write_failure_rolls_back_prior_bytes(self):
        self.write("AGENTS.md", "Original project rules.\r\n")
        self.write(cpo.CONFIG, '# Preserve this\nmodel = "original"\n')
        before = self.tree()
        real_write = cpo.atomic_write
        failed = False

        def fail_once(root, relative, value, created):
            nonlocal failed
            if relative == ".codex/agents/cpo_worker.toml" and not failed:
                failed = True
                raise OSError("simulated write failure")
            return real_write(root, relative, value, created)

        with patch.object(cpo, "atomic_write", side_effect=fail_once), self.assertRaises(OSError):
            self.install()
        self.assertEqual(self.tree(), before)
        self.assertFalse((self.project / cpo.STATE_DIR).exists())

    def test_uninstall_failure_rolls_back_to_installed_state(self):
        self.write("AGENTS.md", "Original")
        self.install()
        before = self.tree()
        real_write = cpo.atomic_write
        failed = False

        def fail_once(root, relative, value, created):
            nonlocal failed
            if relative == cpo.CONFIG and not failed:
                failed = True
                raise OSError("simulated restore failure")
            return real_write(root, relative, value, created)

        with patch.object(cpo, "atomic_write", side_effect=fail_once), self.assertRaises(OSError):
            self.uninstall()
        self.assertEqual(self.tree(), before)
        self.assertEqual(self.run_quiet(cpo.status, self.project), 0)

    def test_incomplete_rollback_retains_backups_and_concurrent_edit(self):
        original_config = b'model = "before"\n'
        self.write(cpo.CONFIG, original_config)
        real_write = cpo.atomic_write
        injected = False

        def fail_after_external_edit(root, relative, value, created):
            nonlocal injected
            if relative == ".codex/agents/cpo_worker.toml" and not injected:
                injected = True
                (root / cpo.CONFIG).write_bytes(b'model = "external-change"\n')
                raise OSError("write failed after an unrelated concurrent edit")
            return real_write(root, relative, value, created)

        with patch.object(cpo, "atomic_write", side_effect=fail_after_external_edit), self.assertRaises(cpo.InstallError):
            self.install()
        self.assertEqual((self.project / cpo.CONFIG).read_bytes(), b'model = "external-change"\n')
        self.assertEqual((self.project / cpo.original_path(cpo.CONFIG)).read_bytes(), original_config)

    def test_cli_install_status_and_uninstall(self):
        for command in ("install", "status", "uninstall"):
            result = subprocess.run(
                [sys.executable, str(ROOT / "install.py"), command, "--project", str(self.project)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_separate_projects_have_independent_state(self):
        other = self.base / "second-project"
        other.mkdir()
        self.install()
        before = self.tree()
        self.run_quiet(cpo.install, other, mode="economy")
        self.assertEqual(self.tree(), before)
        self.run_quiet(cpo.uninstall, other)
        self.assertEqual(self.tree(), before)

    def test_status_before_install_is_read_only(self):
        self.assertEqual(self.run_quiet(cpo.status, self.project), 1)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_unrelated_agents_and_gitignore_survive_uninstall(self):
        self.write(".codex/agents/team.toml", 'name = "team"\n')
        self.write(cpo.IGNORE, "# team ignore\ncache/\n")
        before = self.tree()
        self.install()
        self.uninstall()
        self.assertEqual(self.tree(), before)

    def test_new_files_after_install_are_not_removed(self):
        self.install()
        self.write(".codex/agents/new-role.toml", 'name = "new-role"\n')
        self.uninstall()
        self.assertEqual(self.tree(), {".codex/agents/new-role.toml": b'name = "new-role"\n'})


if __name__ == "__main__":
    unittest.main()
