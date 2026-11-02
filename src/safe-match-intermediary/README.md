# Safe Match intermediary

Investigators who hold the same or similar images rarely know about each other. The
UMass Safe Matching service connects them by comparing **essays**: short text
descriptions of images that RescueBox writes and strips of personal information. This
service is the only part of RescueBox that talks to UMass. It holds the agency's
credentials, queues uploads so that ingestion never waits on the network, and answers
similarity queries. RescueBox plugins call it on `127.0.0.1` through the client in
`rb.lib.safe_match`, the same way the frontend calls the backend.

## What leaves this machine

Nothing is sent until an administrator enables the service with UMass credentials.
After that:

- **Each upload sends:** an essay (already redacted by RescueBox), the file's SHA-256
  hash, the investigator's email address and, optionally, the file name.
- **Each query sends:** an essay. It returns the hashes, similarity distances,
  investigator emails and file names of similar files that others hold.

Evidence files and images never leave, and UMass never returns essays.

## Enable it (administrators)

1. **Get credentials.** Ask the UMass Safe Matching operator for credentials for this
   server. They run `tools/clients.py create "<agency, contact>"` in semantic-match-api
   and give you a JSON file through a secret store. New credentials work only after UMass
   redeploys its service; until then the status shows `unauthorized`.
2. **Install the file.** Save it as `~/.rescuebox/safe-match/credentials.json`, then run
   `chmod 600` on the file and `chmod 700` on the directory.
3. **Start the service** from the repository root with `bash startup/safe_match_start.sh`.
   It builds and starts the `rb-safe-match` container, which Docker restarts after
   reboots. Run it again after upgrading RescueBox, or after replacing the credentials.
4. **Check it:** `curl http://127.0.0.1:8090/v1/status` should report `"remote": "ok"`.

Without Docker, run it in the RescueBox environment instead:
`poetry install --with safe-match`, then `poetry run python -m safe_match_intermediary`.
The Windows installer does not include the service yet, so plugins there report that
Safe Match is not enabled.

## Configuration

Environment variables, all optional:

| Variable | Default | Purpose |
|---|---|---|
| `RESCUEBOX_SAFE_MATCH_MODE` | `live` | `stub` serves simulated matches and sends nothing (see below). |
| `RESCUEBOX_SAFE_MATCH_DATA_DIR` | `~/.rescuebox/safe-match` (Windows: `%LOCALAPPDATA%\RescueBox\safe-match`) | Holds the upload queue, `outbox.db`. |
| `RESCUEBOX_SAFE_MATCH_CREDENTIALS` | `<DATA_DIR>/credentials.json` | The UMass credentials file. Read at startup. |
| `RESCUEBOX_SAFE_MATCH_PORT` | `8090` | Port on 127.0.0.1. Plugins read it too. |
| `RESCUEBOX_SAFE_MATCH_URL`, `RESCUEBOX_SAFE_MATCH_TIMEOUT` | `http://127.0.0.1:8090`, `60` s | Used by the plugin client only. |
| `HTTPS_PROXY`, `SSL_CERT_FILE` | none | Agency proxy and certificate authority for reaching UMass. |

`RESCUEBOX_SAFE_MATCH_HOST` exists only so the Docker image can listen inside its
container. That container's port is published on the host's loopback interface. Never
expose the service to the network: it has no authentication of its own.

## Status and troubleshooting

`GET /v1/status` reports the mode, whether credentials are configured, the state of the
connection to UMass, and the number of queued (`pending`) and refused (`failed`) uploads.

| `remote` | Meaning | What to do |
|---|---|---|
| `ok` | The last call to UMass worked. | Nothing. |
| `unchecked` | No call has finished yet. | Check again in a few seconds. |
| `credentials_missing`, `credentials_invalid` | The credentials file is absent or malformed. | Install the file as above, then restart. |
| `unauthorized` | UMass rejected the credentials. | New credentials need a UMass redeploy; otherwise ask UMass. |
| `forbidden` | The credentials lack the upload or query permission. | Ask UMass to reissue them. |
| `unavailable` | UMass could not be reached. | Uploads stay queued and resume on their own; check the proxy settings. |

While UMass is unavailable or rejects the credentials, uploads stay queued, and the
service retries with backoff of up to five minutes. `failed` counts uploads that UMass
refused as invalid. Uploading the same file again replaces them. Logs
(`docker logs rb-safe-match`) record events, statuses and error codes only, never
essays, emails, hashes, file names or tokens.

## Stub mode

With `RESCUEBOX_SAFE_MATCH_MODE=stub`, an in-process imitation of UMass stands in for
the real service. It ranks essays by shared words, keeps everything in memory, and
forgets it on restart. Nothing leaves the machine. Use it to develop and demonstrate
plugins without credentials.

## Local API

Requests and responses are JSON. Requests must send `Content-Type: application/json`
and address `127.0.0.1` or `localhost`, which keeps web pages from using the service.

| Endpoint | Body | Response |
|---|---|---|
| `POST /v1/upload` | `sha256`, `investigator_email`, `essay_version`, `essay`, optional `file_name` | `202 {sha256, essay_version, delivery: "queued"}` once the upload is stored. |
| `POST /v1/query` | `essay`, optional `top_k` (1–1000, default 10) | `200 {model, matches: [{sha256, distance, essay_version, investigators}]}`, closest first. |
| `GET /v1/status` | none | See above. |

Fields are validated exactly as UMass validates them.

**Errors** have the form `{"error": {"code", "message", "details": {"fields"}}}`, and
messages never repeat submitted values:

| Code | Status | Meaning |
|---|---|---|
| `invalid_request` | 400 | A field is wrong. |
| `unsupported_media_type` | 415 | The body is not declared as JSON. |
| `payload_too_large` | 413 | The body is too large. |
| `not_configured` | 503 | No valid credentials. |
| `remote_unauthorized`, `remote_forbidden`, `remote_unavailable` | 503 | A query reached UMass and failed. |

A query stores nothing. To share a query's essay as well, upload it after querying; the
upload then goes through the durable queue.

## Behavior worth knowing

- **Merging.** Uploads for the same file and investigator are merged while they wait.
  UMass ends up in the same state as if each had been sent: a newer essay version
  replaces an older one, and a file name is kept when a later upload omits it.
- **Crashes.** An upload interrupted by a crash or restart is sent again. UMass treats
  repeated uploads as one.
- **Credential changes.** Queued uploads go to whichever UMass deployment the current
  credentials name, for example after switching from staging to production.

## Development

```sh
poetry install --with safe-match --with dev
poetry run pytest src/safe-match-intermediary/tests src/rb-lib/rb/lib/tests/test_safe_match.py -q
RUN_INTEGRATION=1 RESCUEBOX_SAFE_MATCH_CREDENTIALS=/path/to/staging.json \
  poetry run pytest src/safe-match-intermediary/tests/test_sm_live.py
```

| Module | Role |
|---|---|
| `app.py` | HTTP layer |
| `outbox.py` | Durable queue and delivery worker |
| `remote.py` | Tokens, calls to UMass, error classes |
| `schemas.py` | Validation, ported from semantic-match-api `service/match_service/schemas.py`; keep the two in step |
| `stub.py` | The imitation used by stub mode and the tests |

The pinned versions in the `Dockerfile` must match `poetry.lock`.
