from evaluation.run_all import run


def test_run_helper_builds_python_module_command(monkeypatch) -> None:
    commands = []
    monkeypatch.setattr("subprocess.run", lambda command, check: commands.append((command, check)))
    run("example.module", "--value", "1")
    assert commands[0][0][1:] == ["-m", "example.module", "--value", "1"]