#!/usr/bin/env python3
"""Smoke-test the Safe Match intermediary: start one, upload and query, then stop it.

Runs the intermediary natively or in Docker, in stub mode (a simulated UMass, so
nothing leaves this machine) or live mode (the UMass API, through a credentials file).
Uploads two synthetic essays, waits for their delivery, and checks that a paraphrase
finds its original ahead of the unrelated essay. Also checks that query responses and
the intermediary's log hold no essays, emails, hashes, file names or secrets. Live
runs reuse fixed synthetic hashes with a new essay version each time, so they do not
grow the UMass corpus.

Asks for every input not given as a switch before anything starts; --yes answers
every question with its default instead. Exits 0 on PASS.
"""

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from rb.lib.safe_match import SafeMatchClient, SafeMatchError
from safe_match_intermediary.config import (
    Credentials,
    CredentialsError,
    Settings,
    load_credentials,
)

HERE = Path(__file__).resolve().parent
IMAGE = "rescuebox-safe-match-smoketest"
SECRET = "/run/secrets/safe-match-credentials.json"
ESSAYS = {
    "original": "A red bicycle leans against a brick wall beside a wooden door.",
    "unrelated": "A bowl of oranges sits on a kitchen table under a window.",
}
PARAPHRASE = "A red bike rests against a brick wall next to a door."
INVESTIGATOR = "smoketest@example.org"
MODE = "Mode (stub: simulated UMass, nothing leaves this machine; live: the UMass API)"
RUNTIME = "Runtime (native: a Python process; docker: a container from the Dockerfile)"
HINTS = {
    "credentials_missing": "the intermediary found no credentials file",
    "credentials_invalid": "the intermediary could not use the credentials file",
    "unauthorized": "UMass rejected the credentials (new ones work after it redeploys)",
    "forbidden": "the credentials lack the upload or query permission",
    "unavailable": "UMass could not be reached; check the network and HTTPS_PROXY",
}
Ask = Callable[[str], str]


class SmokeError(Exception):
    """A failed check, described without essays or credentials."""


@dataclass(frozen=True)
class Inputs:
    mode: str
    runtime: str
    credentials_file: Path | None
    credentials: Credentials | None
    timeout: int


@dataclass(frozen=True)
class Server:
    url: str
    alive: Callable[[], bool]


def say(message: str) -> None:
    print(message, flush=True)


def synthetic_sha256(label: str) -> str:
    """The hashes of semantic-match-api's smoke test, so the two share UMass rows."""
    return hashlib.sha256(f"semantic-match-smoketest/{label}".encode()).hexdigest()


def api_host(credentials: Credentials) -> str:
    return urlsplit(credentials.api_url).hostname or ""


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    root.add_argument("--mode", choices=["stub", "live"], help="default: stub")
    root.add_argument("--runtime", choices=["native", "docker"], help="default: native")
    root.add_argument(
        "--credentials",
        help="the UMass credentials file for live mode "
        f"(default: {Settings.from_env().credentials_path})",
    )
    root.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="answer every question with its default, including the live confirmation",
    )
    root.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="seconds to wait for delivery and for indexing (default: 600)",
    )
    return root


def choose(args: argparse.Namespace, ask: Ask | None) -> Inputs:
    """Settles every input before anything starts; without ask, takes defaults."""
    mode = resolve(args.mode, "--mode", MODE, "stub", one_of("stub", "live"), ask)
    runtime = resolve(args.runtime, "--runtime", RUNTIME, "native", usable, ask)
    if mode == "stub":
        return Inputs(mode, runtime, None, None, args.timeout)
    default = str(Settings.from_env().credentials_path)
    path, credentials = resolve(
        args.credentials, "--credentials", "Credentials file", default, readable, ask
    )
    host = api_host(credentials)
    question = f"Send two synthetic essays to the UMass API at {host}? (yes/no)"
    if not resolve(None, "--yes", question, "yes", yes_or_no, ask):
        raise SystemExit("Stopped; nothing was sent.")
    return Inputs(mode, runtime, path, credentials, args.timeout)


def resolve(
    given: str | None,
    switch: str,
    question: str,
    default: str,
    parse: Callable[[str], Any],
    ask: Ask | None,
) -> Any:
    """A switch's value, else an answer (asked until it parses), else the default."""
    if given is not None or ask is None:
        try:
            return parse(default if given is None else given)
        except ValueError as error:
            raise SystemExit(f"{switch}: {error}") from None
    while True:
        try:
            return parse(ask(f"{question} [{default}]: ").strip() or default)
        except ValueError as error:
            say(f"  {error}")
        except EOFError:
            raise SystemExit(f"No answer; pass {switch} or --yes.") from None


def one_of(*options: str) -> Callable[[str], str]:
    def parse(answer: str) -> str:
        if answer.lower() not in options:
            raise ValueError(f"Answer {' or '.join(options)}.")
        return answer.lower()

    return parse


def usable(answer: str) -> str:
    """A runtime that can start here."""
    runtime = one_of("native", "docker")(answer)
    if runtime == "docker" and not docker_running():
        raise ValueError("Docker is not running; start it, or choose native.")
    return runtime


def docker_running() -> bool:
    try:
        info = subprocess.run(["docker", "info"], capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return info.returncode == 0


def readable(answer: str) -> tuple[Path, Credentials]:
    """A credentials file that the intermediary will accept."""
    path = Path(answer).expanduser().resolve()
    try:
        return path, load_credentials(path)
    except CredentialsError as error:
        raise ValueError(str(error)) from None


def yes_or_no(answer: str) -> bool:
    if answer.lower() not in ("yes", "y", "no", "n"):
        raise ValueError("Answer yes or no.")
    return answer.lower().startswith("y")


@contextmanager
def native(inputs: Inputs, data: Path, logs: Path) -> Iterator[Server]:
    """python -m safe_match_intermediary, as a child process on a free port."""
    port = free_port()
    env = {**os.environ, **server_env(inputs, port, data), "PYTHONPATH": python_path()}
    with open(logs / "intermediary.log", "wb") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "safe_match_intermediary"],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    say(f"  Started process {process.pid} on port {port}.")
    try:
        yield Server(f"http://127.0.0.1:{port}", lambda: process.poll() is None)
    finally:
        process.terminate()
        try:
            process.wait(30)
        except subprocess.TimeoutExpired:
            process.kill()


def server_env(inputs: Inputs, port: int, data: Path) -> dict[str, str]:
    env = {
        "RESCUEBOX_SAFE_MATCH_MODE": inputs.mode,
        "RESCUEBOX_SAFE_MATCH_HOST": "127.0.0.1",
        "RESCUEBOX_SAFE_MATCH_PORT": str(port),
        "RESCUEBOX_SAFE_MATCH_DATA_DIR": str(data),
    }
    if inputs.credentials_file:
        env["RESCUEBOX_SAFE_MATCH_CREDENTIALS"] = str(inputs.credentials_file)
    return env


def python_path() -> str:
    """Lets the child import the intermediary whether or not it is installed."""
    return os.pathsep.join(filter(None, [str(HERE), os.getenv("PYTHONPATH")]))


@contextmanager
def docker(inputs: Inputs, data: Path, logs: Path) -> Iterator[Server]:
    """The image built from this directory, in a container of its own."""
    say("  Building the image; a first build takes a few minutes.")
    run(["docker", "build", "--tag", IMAGE, str(HERE)], logs / "docker-build.log")
    name, port = f"rb-safe-match-smoketest-{os.getpid()}", free_port()
    command = ["docker", "run", "--detach", "--name", name]
    command += [*container_options(inputs, port, data), IMAGE]
    try:
        run(command, logs / "docker-run.log")
        say(f"  Started container {name} on port {port}.")
        yield Server(f"http://127.0.0.1:{port}", lambda: container_running(name))
    finally:
        with open(logs / "intermediary.log", "wb") as log:
            subprocess.run(["docker", "logs", name], stdout=log, stderr=log)
        subprocess.run(["docker", "rm", "--force", name], capture_output=True)


def container_options(inputs: Inputs, port: int, data: Path) -> list[str]:
    """Those of startup/docker-compose.yml, on a free port and with the inputs."""
    options = ["--publish", f"127.0.0.1:{port}:8090", "--volume", f"{data}:/data"]
    options += ["--env", f"RESCUEBOX_SAFE_MATCH_MODE={inputs.mode}"]
    if hasattr(os, "getuid"):
        options += ["--user", f"{os.getuid()}:{os.getgid()}"]
    if inputs.credentials_file:
        options += ["--volume", f"{inputs.credentials_file}:{SECRET}:ro"]
        options += ["--env", f"RESCUEBOX_SAFE_MATCH_CREDENTIALS={SECRET}"]
    return options


def container_running(name: str) -> bool:
    inspect = ["docker", "inspect", "--format", "{{.State.Running}}", name]
    state = subprocess.run(inspect, capture_output=True, text=True).stdout
    return state.strip() == "true"


def run(command: list[str], log_path: Path) -> None:
    with open(log_path, "wb") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise SmokeError(f"{' '.join(command[:2])} failed; see {log_path.name}.")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


RUNTIMES = {"native": native, "docker": docker}


def wait_for_start(sdk: SafeMatchClient, server: Server) -> None:
    for _ in waiting(60, "the intermediary to start", 0.5):
        if sdk.status() is not None:
            return
        if not server.alive():
            raise SmokeError("The intermediary stopped; see intermediary.log.")


def check(sdk: SafeMatchClient, timeout: float) -> str:
    """Phases 2 to 4 against a running intermediary; returns what the query found."""
    say("[2/5] Check the connection to UMass")
    status = connected(sdk)
    say(f"  Mode {status['mode']}, connection {status['remote']}.")
    say("[3/5] Upload two synthetic essays and wait for their delivery")
    version = int(time.time())
    for label, essay in ESSAYS.items():
        sdk.upload(
            sha256=synthetic_sha256(label),
            investigator_email=INVESTIGATOR,
            essay_version=version,
            essay=essay,
            file_name=f"smoketest-{label}.txt",
        )
    delivered(sdk, timeout)
    say("[4/5] Query a paraphrase until it finds its original")
    return found(sdk, timeout)


def connected(sdk: SafeMatchClient) -> dict:
    """The status once the intermediary has checked its connection to UMass."""
    for _ in waiting(60, "the connection check", 0.5):
        status = current(sdk)
        if status["remote"] == "ok":
            return status
        if status["remote"] != "unchecked":
            raise SmokeError(problem(status))


def delivered(sdk: SafeMatchClient, timeout: float) -> None:
    for _ in waiting(timeout, "delivery to UMass", 0.5):
        status = current(sdk)
        if status["outbox"]["failed"]:
            raise SmokeError("UMass refused an upload as invalid.")
        if not status["outbox"]["pending"]:
            return
        if status["remote"] in ("unauthorized", "forbidden"):
            raise SmokeError(problem(status))


def found(sdk: SafeMatchClient, timeout: float) -> str:
    """Queries until UMass has indexed the original, which must outrank the other."""
    original, unrelated = synthetic_sha256("original"), synthetic_sha256("unrelated")
    for _ in waiting(timeout, "UMass to index the essays", 5):
        started = time.monotonic()
        try:
            result = sdk.query(PARAPHRASE)
        except SafeMatchError as error:
            if not error.retryable:
                raise
            continue
        seconds = time.monotonic() - started
        if any(text in json.dumps(result) for text in [*ESSAYS.values(), PARAPHRASE]):
            raise SmokeError("A query response contained essay text.")
        distances = {match["sha256"]: match["distance"] for match in result["matches"]}
        if original in distances:
            if distances.get(unrelated, float("inf")) < distances[original]:
                raise SmokeError("The unrelated essay ranked above the original.")
            return (
                f"the paraphrase found its original at distance {distances[original]:.3f}"
                f" with model {result['model']} in {seconds:.2f} s"
            )


def current(sdk: SafeMatchClient) -> dict:
    status = sdk.status()
    if status is None:
        raise SmokeError("The intermediary stopped answering; see intermediary.log.")
    return status


def problem(status: dict) -> str:
    return f"The connection to UMass is {status['remote']}: {HINTS[status['remote']]}."


def waiting(seconds: float, what: str, interval: float) -> Iterator[None]:
    """Paces a polling loop: reports every 30 s and fails once the time is up."""
    started = reported = time.monotonic()
    while time.monotonic() - started < seconds:
        yield
        time.sleep(interval)
        if time.monotonic() - reported >= 30:
            reported = time.monotonic()
            say(f"  Still waiting for {what} ({reported - started:.0f} s).")
    raise SmokeError(f"Gave up waiting for {what} after {seconds:.0f} s.")


def check_log(log: Path, credentials: Credentials | None) -> None:
    """The log must hold no essays, emails, hashes, file names or secrets."""
    text = log.read_text(errors="replace")
    private = {
        "essay text": [*ESSAYS.values(), PARAPHRASE],
        "an email address": [INVESTIGATOR],
        "a file hash": [synthetic_sha256(label) for label in ESSAYS],
        "a file name": [f"smoketest-{label}.txt" for label in ESSAYS],
        "the client secret": [credentials.client_secret] if credentials else [],
    }
    for kind, values in private.items():
        if any(value in text for value in values):
            raise SmokeError(f"The intermediary's log contains {kind}.")


def smoke(inputs: Inputs, logs: Path) -> str:
    """All five phases; returns what the query found."""
    target = f" against {api_host(inputs.credentials)}" if inputs.credentials else ""
    say(f"[1/5] Start the intermediary ({inputs.runtime}, {inputs.mode} mode{target})")
    with (
        tempfile.TemporaryDirectory(prefix="safe-match-smoketest-data-") as data,
        RUNTIMES[inputs.runtime](inputs, Path(data), logs) as server,
        closing(SafeMatchClient(server.url)) as sdk,
    ):
        wait_for_start(sdk, server)
        summary = check(sdk, inputs.timeout)
    say("[5/5] Check the intermediary's log")
    check_log(logs / "intermediary.log", inputs.credentials)
    return summary


def report(inputs: Inputs, logs: Path) -> int:
    try:
        summary = smoke(inputs, logs)
    except (SmokeError, SafeMatchError) as error:
        say(f"FAIL: {error} (logs: {logs})")
        return 1
    say(f"PASS: {summary} (logs: {logs})")
    return 0


def main(argv: list[str] | None = None, ask: Ask = input) -> int:
    args = parser().parse_args(argv)
    say("Safe Match intermediary smoke test")
    try:
        inputs = choose(args, None if args.yes else ask)
        return report(inputs, Path(tempfile.mkdtemp(prefix="safe-match-smoketest-")))
    except KeyboardInterrupt:
        say("\nStopped.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
