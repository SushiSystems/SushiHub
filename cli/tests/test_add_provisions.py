"""Bringing a module in brings its dependencies with it."""

from sushistack.services import modules


def test_add_provisions_once_after_a_new_clone(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(modules, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(modules, "registered_modules", lambda: {})
    monkeypatch.setattr(modules, "_run_git", lambda args, cwd: (tmp_path / "sushiruntime" / ".git").mkdir(parents=True) or 0)
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)
    rc = modules.add(["sushiruntime"], provision=lambda dry_run: calls.append(dry_run) or 0)
    assert rc == 0 and calls == [False]


def test_add_skips_provision_when_nothing_new(monkeypatch, tmp_path):
    (tmp_path / "sushiruntime" / ".git").mkdir(parents=True)
    calls = []
    monkeypatch.setattr(modules, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(modules, "registered_modules", lambda: {})
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)
    modules.add(["sushiruntime"], provision=lambda dry_run: calls.append(dry_run) or 0)
    assert calls == []


def test_add_honours_skip_install(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(modules, "workspace_root", lambda: tmp_path)
    monkeypatch.setattr(modules, "registered_modules", lambda: {})
    monkeypatch.setattr(modules, "_run_git", lambda args, cwd: (tmp_path / "sushiruntime" / ".git").mkdir(parents=True) or 0)
    monkeypatch.setattr(modules, "_install_module_cli", lambda *a, **k: True)
    modules.add(["sushiruntime"], skip_install=True, provision=lambda dry_run: calls.append(dry_run) or 0)
    assert calls == []
