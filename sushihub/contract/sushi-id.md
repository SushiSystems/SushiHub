# Sushi ID: the six endpoints `hub` calls

`hub login`, `hub logout`, `hub whoami` and `hub license` sign a machine in and read the account;
`hub add sushiengine` and `hub update sushiengine` ask for a licence token and a release. None of the
six exists in sushiweb yet. This page is the agreement between the two repositories: `hub` is built
against it and tested against a fake server that implements it
(`sushihub/cli/tests/test_identity.py`), and sushiweb builds the real one to the same shapes.

The design behind it is `docs/agent/specs/2026-09-05-hub-design.md`, section 6, and sushiweb's own
`docs/agent/specs/2026-09-05-device-grant-and-releases-design.md`, sections 5 and 6.

## The endpoints

Bodies are JSON in both directions; every request carries `Content-Type: application/json`.

| Method and path | Request | Response |
|---|---|---|
| `POST /api/device/code` | `{"client_id": "sushihub"}` | `{"device_code", "user_code", "verification_uri", "expires_in", "interval"}` |
| `POST /api/device/token` | `{"client_id": "sushihub", "device_code"}` | `200 {"access_token", "refresh_token", "expires_in"}` or `400 {"error": "authorization_pending" \| "slow_down" \| "expired_token" \| "access_denied"}` |
| `POST /api/token/refresh` | `{"refresh_token"}` | `200 {"access_token", "expires_in"}` or `401` |
| `GET /api/me` (Bearer) | | `{"account_id", "email", "licenses": [{"product", "holder": "account" \| "org", "expires_at": iso-8601 or null}]}` |
| `POST /api/licenses/token` (Bearer) | `{"product"}` | `200 {"licence_token", "expires_at"}`; `403 {"error": "no_licence"}`; `404 {"error": "unknown_product"}` |
| `POST /api/releases/resolve` (Bearer) | `{"product", "platform", "version"?}` | `200 {"version", "platform", "url", "sha256", "size", "expires_at"}`; `403 no_licence`; `404 unknown_product` or `no_release`; `429` |

`expires_in` is seconds from the moment the response is written. `interval` is the seconds `hub`
waits between two polls. `verification_uri` is the page a person opens to type `user_code`.

The base URL comes from `sushihub/cli/config.toml`'s `[identity] url`, which ships as
`https://id.sushisystems.io`, and `SUSHI_ID_URL` overrides it.

## The device grant, step by step

1. `hub login` posts to `/api/device/code` and receives a device code, a user code and the
   verification URI.
2. It prints the user code and the URI, then opens the URI in the browser. A person signs in
   there and types the user code.
3. Meanwhile `hub` posts to `/api/device/token` every `interval` seconds. While the person has not
   finished, the endpoint answers `400 authorization_pending`. `slow_down` means the same and
   doubles the interval `hub` uses from then on. `access_denied` and `expired_token` end the login
   with a message.
4. On the first `200`, `hub` stores the access token, the refresh token and the expiry in the
   operating system's credential store through `keyring`, under service `sushistack` and username
   `sushi-id`.
5. Every later command reads the store. Within 30 seconds of the access token's expiry it posts
   the refresh token to `/api/token/refresh` and stores the new access token. A `401` there means
   the session is gone and the command reports that nobody is signed in.

`hub logout` deletes the stored entry and calls nothing.

## Licences

`hub whoami` and `hub license` both read `/api/me`. `holder` is `account` when the licence belongs to
the person and `org` when it comes from an organization seat. `expires_at` is null for a licence
that does not expire. `hub` decides nothing about a licence: it asks for a download URL and Sushi ID
answers or refuses.

## Releases and the licence file

`hub add sushiengine` derives a platform string, `windows-x64` or `linux-x64`, from
`platform.system()` and `platform.machine()`, and posts it with the product to
`/api/releases/resolve`. The answer carries a signed URL that lives ten minutes, the archive's
`sha256` and its `size`. `hub` downloads it, refuses to unpack it when either does not match, and
unpacks it into `<workspace>/sushiengine`. Omitting `version` asks for the latest release, which is
what `hub update` does to find out whether a newer one exists.

`hub` then posts the product to `/api/licenses/token` and writes what comes back, the bare token and
nothing else, to `<workspace>/sushiengine/sushi-licence.jwt`. The token is an Ed25519 JWT whose
`exp` is the earlier of the licence's expiry and thirty days from issue; the engine reads the file
at start-up and verifies it offline against `/.well-known/jwks.json`. Renewal is `hub`'s job, and
`hub update sushiengine` writes the file again. What the engine does once the token has expired is
the engine's own design, not this page's.
