# Sushi ID: the four endpoints `ss` calls

`ss login`, `ss logout`, `ss whoami` and `ss license` speak to Sushi ID over four HTTP endpoints.
None of them exists in sushiweb yet. This page is the agreement between the two repositories: `ss`
is built against it and tested against a fake server that implements it
(`cli/tests/test_identity.py`), and sushiweb builds the real one to the same shapes.

The design behind it is `docs/agent/specs/2026-09-05-hub-design.md`, section 6.

## The endpoints

Bodies are JSON in both directions; every request carries `Content-Type: application/json`.

| Method and path | Request | Response |
|---|---|---|
| `POST /api/device/code` | `{"client_id": "ss"}` | `{"device_code", "user_code", "verification_uri", "expires_in", "interval"}` |
| `POST /api/device/token` | `{"client_id": "ss", "device_code"}` | `200 {"access_token", "refresh_token", "expires_in"}` or `400 {"error": "authorization_pending" \| "slow_down" \| "expired_token" \| "access_denied"}` |
| `POST /api/token/refresh` | `{"refresh_token"}` | `200 {"access_token", "expires_in"}` or `401` |
| `GET /api/me` (Bearer) | | `{"account_id", "email", "licenses": [{"product", "holder": "account" \| "org", "expires_at": iso-8601 or null}]}` |

`expires_in` is seconds from the moment the response is written. `interval` is the seconds `ss`
waits between two polls. `verification_uri` is the page a person opens to type `user_code`.

The base URL comes from `cli/config.toml`'s `[identity] url`, which ships as
`https://id.sushisystems.io`, and `SUSHI_ID_URL` overrides it.

## The device grant, step by step

1. `ss login` posts to `/api/device/code` and receives a device code, a user code and the
   verification URI.
2. It prints the user code and the URI, then opens the URI in the browser. A person signs in
   there and types the user code.
3. Meanwhile `ss` posts to `/api/device/token` every `interval` seconds. While the person has not
   finished, the endpoint answers `400 authorization_pending`. `slow_down` means the same and
   doubles the interval `ss` uses from then on. `access_denied` and `expired_token` end the login
   with a message.
4. On the first `200`, `ss` stores the access token, the refresh token and the expiry in the
   operating system's credential store through `keyring`, under service `sushistack` and username
   `sushi-id`.
5. Every later command reads the store. Within 30 seconds of the access token's expiry it posts
   the refresh token to `/api/token/refresh` and stores the new access token. A `401` there means
   the session is gone and the command reports that nobody is signed in.

`ss logout` deletes the stored entry and calls nothing.

## Licences

`ss whoami` and `ss license` both read `/api/me`. `holder` is `account` when the licence belongs to
the person and `org` when it comes from an organization seat. `expires_at` is null for a licence
that does not expire. `ss` does not decide whether a licence is live; wave 5's `ss add sushiengine`
asks Sushi ID for a download URL and Sushi ID answers or refuses.
