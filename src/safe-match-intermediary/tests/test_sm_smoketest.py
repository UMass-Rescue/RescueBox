import tempfile
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import smoketest
from rb.lib.safe_match import SafeMatchClient
from safe_match_intermediary.app import create_app
from safe_match_intermediary.config import Settings, load_credentials
from safe_match_intermediary.stub import FakeApi


def replies(*answers: str) -> tuple[list[str], Callable[[str], str]]:
    """An input() stand-in that gives these answers and records the questions."""
    asked, queue = [], list(answers)

    def ask(question: str) -> str:
        asked.append(question)
        return queue.pop(0)

    return asked, ask


def choose(argv: list[str], ask: Callable[[str], str] | None) -> smoketest.Inputs:
    args = smoketest.parser().parse_args(argv)
    return smoketest.choose(args, None if args.yes else ask)


def serve(settings: Settings, transport: httpx.MockTransport | None) -> TestClient:
    return TestClient(create_app(settings, transport), base_url="http://127.0.0.1")


def test_questions_offer_defaults() -> None:
    asked, ask = replies("", "")
    inputs = choose([], ask)
    assert (inputs.mode, inputs.runtime) == ("stub", "native")
    assert [question.split()[0] for question in asked] == ["Mode", "Runtime"]


def test_switches_leave_only_the_live_confirmation(credentials_file: Path) -> None:
    asked, ask = replies("yes")
    switches = ["--runtime", "native", "--credentials", str(credentials_file)]
    assert choose(["--mode", "stub", *switches], ask).credentials is None
    live = choose(["--mode", "live", *switches], ask)
    assert live.credentials_file == credentials_file
    assert len(asked) == 1 and "api.test.example" in asked[0]


def test_yes_answers_every_question_with_its_default(credentials_file: Path) -> None:
    inputs = choose(
        ["--mode", "live", "--credentials", str(credentials_file), "-y"], None
    )
    assert (inputs.runtime, inputs.credentials.client_id) == ("native", "test-client")


def test_wrong_answers_are_asked_again(
    tmp_path: Path, credentials_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(smoketest, "docker_running", lambda: False)
    absent, present = str(tmp_path / "absent.json"), str(credentials_file)
    asked, ask = replies("remote", "live", "docker", "", absent, present, "maybe", "y")
    inputs = choose([], ask)
    assert (inputs.mode, inputs.runtime) == ("live", "native")
    assert inputs.credentials_file == credentials_file and len(asked) == 8


def test_bad_switches_stop_before_anything_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(smoketest, "docker_running", lambda: False)
    with pytest.raises(SystemExit, match="--runtime: Docker is not running"):
        choose(["--runtime", "docker", "--yes"], None)
    absent = str(tmp_path / "absent.json")
    with pytest.raises(SystemExit, match="--credentials: No credentials file"):
        choose(["--mode", "live", "--credentials", absent, "--yes"], None)


def test_declining_the_confirmation_sends_nothing(credentials_file: Path) -> None:
    _, ask = replies("no")
    switches = ["--mode", "live", "--runtime", "native"]
    with pytest.raises(SystemExit, match="nothing was sent"):
        choose([*switches, "--credentials", str(credentials_file)], ask)


def test_without_input_the_missing_switch_is_named() -> None:
    def closed(question: str) -> str:
        raise EOFError

    with pytest.raises(SystemExit, match="pass --mode or --yes"):
        choose([], closed)


@pytest.mark.parametrize("mode", ["stub", "live"])
def test_the_checks_pass_against_a_working_intermediary(
    mode: str, stub_settings: Settings, live_settings: Settings
) -> None:
    settings = {"stub": stub_settings, "live": live_settings}[mode]
    transport = httpx.MockTransport(FakeApi()) if mode == "live" else None
    with serve(settings, transport) as client:
        summary = smoketest.check(SafeMatchClient(http=client), timeout=10)
    assert summary.startswith("the paraphrase found its original")


def test_rejected_credentials_fail_with_a_hint(live_settings: Settings) -> None:
    api = FakeApi()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/token":
            return httpx.Response(400, json={"error": "invalid_client"})
        return api(request)

    with serve(live_settings, httpx.MockTransport(handler)) as client:
        with pytest.raises(smoketest.SmokeError, match="unauthorized.*redeploys"):
            smoketest.check(SafeMatchClient(http=client), timeout=10)


def test_the_log_check_names_what_leaked(
    tmp_path: Path, credentials_file: Path, credentials: dict
) -> None:
    log, loaded = tmp_path / "intermediary.log", load_credentials(credentials_file)
    for leak, kind in [
        (smoketest.INVESTIGATOR, "an email address"),
        (smoketest.synthetic_sha256("original"), "a file hash"),
        (credentials["client_secret"], "the client secret"),
    ]:
        log.write_text(f"INFO | safe_match_intermediary | {leak}\n")
        with pytest.raises(smoketest.SmokeError, match=kind):
            smoketest.check_log(log, loaded)


def test_containers_use_loopback_and_read_only_credentials(
    tmp_path: Path, credentials_file: Path
) -> None:
    inputs = choose(
        ["--mode", "live", "--credentials", str(credentials_file), "-y"], None
    )
    options = " ".join(smoketest.container_options(inputs, 5555, tmp_path))
    assert "--publish 127.0.0.1:5555:8090" in options
    assert f"{credentials_file}:{smoketest.SECRET}:ro" in options


def test_a_native_stub_run_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    assert smoketest.main(["--yes", "--timeout", "30"]) == 0
    assert "PASS: the paraphrase found its original" in capsys.readouterr().out
    (logs,) = tmp_path.iterdir()  # the data directory is gone; the logs remain
    assert "Application startup complete" in (logs / "intermediary.log").read_text()
