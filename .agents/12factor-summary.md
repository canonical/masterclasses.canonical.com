# 12-factor Packaging Summary

Generated: 2026-06-08  
Skills used: `12factor-fit` → `12factor-rock` → `12factor-charm`

---

## Repo adaptations

These files were added to the repository to satisfy the flask-framework
rockcraft/charmcraft extension contract:

| File | Purpose |
|---|---|
| `app.py` | WSGI entrypoint shim required by the flask-framework extension (`gunicorn 'app:app'`). Bridges paas-charm env names to the names the app expects (see below). |
| `migrate.sh` | Migration entrypoint for paas-charm. Bridges `POSTGRESQL_DB_CONNECT_STRING` → `DATABASE_URL` then runs `alembic upgrade head`. |
| `requirements.txt` | `flask` added as first line — required by the rockcraft flask-framework extension, which checks for the literal package name. |

---

## Rock

**File:** `masterclasses-canonical-com_0.1_amd64.rock`  
**Base:** `ubuntu@24.04` (bare base attempted first; blocked by chisel digest mismatch in rockcraft 1.19.0)  
**Size:** ~148 MB

### Build notes

- `base: ubuntu@24.04` used instead of `base: bare` due to a chisel digest
  mismatch affecting the rockcraft 1.19.0 snap (packages updated in Ubuntu
  archive after the snap was cut). Retry `base: bare` on the next rockcraft
  stable release.
- The CSS build runs inside the rock: `npm install --production` +
  `npm run build-css` in `flask-framework/install-app` override-build.
- `node_modules/vanilla-framework/templates/` is preserved as
  `flask/app/node_modules/vanilla-framework/templates/` — required at runtime
  by the `ChoiceLoader` in `webapp/app.py`.
- `flask/app/alembic/`, `flask/app/alembic.ini`, `flask/app/events/`,
  `flask/app/models/`, `flask/app/scripts/`, `flask/app/webapp/` are all
  explicitly staged and primed (not in the extension defaults).

### Push command (once registry is known)

```bash
rockcraft.skopeo copy --insecure-policy \
  oci-archive:masterclasses-canonical-com_0.1_amd64.rock \
  docker://<registry>/masterclasses-canonical-com:0.1
```

---

## Charm

**File:** `charm/masterclasses-canonical-com_amd64.charm`  
**Extension:** `flask-framework`  
**Base:** `ubuntu@24.04`

### Env bridge

paas-charm Flask injects user config as `FLASK_<KEY>` and the postgresql
relation as `POSTGRESQL_DB_CONNECT_STRING`. The app reads unqualified env
names. The bridge lives in the root `app.py` shim and in `migrate.sh`.

| paas-charm injects | App reads |
|---|---|
| `POSTGRESQL_DB_CONNECT_STRING` | `DATABASE_URL` |
| `FLASK_ADMIN_EMAILS` | `ADMIN_EMAILS` |
| `FLASK_API_TOKEN` | `API_TOKEN` |
| `FLASK_BASE_URL` | `BASE_URL` |
| `FLASK_CLIENT_EMAIL` | `CLIENT_EMAIL` |
| `FLASK_CLIENT_ID` | `CLIENT_ID` |
| `FLASK_CLIENT_X509_CERT_URL` | `CLIENT_X509_CERT_URL` |
| `FLASK_DIRECTORY_API_TOKEN` | `DIRECTORY_API_TOKEN` |
| `FLASK_GMAIL_DELEGATE_ACCOUNT` | `GMAIL_DELEGATE_ACCOUNT` |
| `FLASK_GOOGLE_PROJECT_ID` | `GOOGLE_PROJECT_ID` |
| `FLASK_MATTERMOST_DEV_WEBHOOK_URL` | `MATTERMOST_DEV_WEBHOOK_URL` |
| `FLASK_OPENID_LAUNCHPAD_TEAM` | `OPENID_LAUNCHPAD_TEAM` |
| `FLASK_PRIVATE_KEY` | `PRIVATE_KEY` |
| `FLASK_PRIVATE_KEY_ID` | `PRIVATE_KEY_ID` |
| `FLASK_SECRET_KEY` | `SECRET_KEY` (handled by `get_flask_env`, no bridge needed) |

### Relations

| Relation | Interface | Optional |
|---|---|---|
| `postgresql` | `postgresql_client` | **no** (app fails to start without `DATABASE_URL`) |
| `ingress` | `ingress` | no (extension) |
| `logging` | `loki_push_api` | yes (extension) |
| `grafana-dashboard` | `grafana_dashboard` | yes (extension) |
| `metrics-endpoint` | `prometheus_scrape` | yes (extension) |

### Config options

| Option | Type | Default | Notes |
|---|---|---|---|
| `flask-secret-key` | secret | — | **Required.** Built-in. `get_flask_env` finds `FLASK_SECRET_KEY`. |
| `openid-launchpad-team` | string | `canonical` | Launchpad team for SSO login restriction. |
| `admin-emails` | string | — | Comma-separated admin emails for notifications. |
| `google-project-id` | string | — | GCP project for Gmail service account. |
| `private-key-id` | string | — | Service account key ID (from JSON key file). |
| `client-email` | string | — | Service account client email. |
| `client-id` | string | — | Service account client ID. |
| `client-x509-cert-url` | string | — | Service account x509 cert URL. |
| `gmail-delegate-account` | string | — | Gmail address the service account sends as. |
| `api-token` | secret | — | Internal API authentication token. |
| `directory-api-token` | secret | — | Canonical directory API token (presenter sync). |
| `mattermost-dev-webhook-url` | secret | — | Mattermost webhook URL for dev notifications. |
| `private-key` | secret | — | Service account PEM private key. Encode newlines as literal `\n`. |
| `webserver-workers` | int | 1 | **Recommended: keep at 1** to avoid duplicate APScheduler jobs. |

### Known constraints

- **APScheduler + multiple workers:** `flask_apscheduler` starts in every
  gunicorn worker. With `webserver-workers > 1`, the scheduled presenter-sync
  job runs N times concurrently. Default to `webserver-workers=1`.
- **Google service account vars are optional at startup** — missing values
  cause email notifications to silently fail but do not crash the app.

---

## Next step: deploy

The three packaging skills (`12factor-fit`, `12factor-rock`, `12factor-charm`)
are complete. The deploy step must be done manually. Once the following are
known, proceed with the commands below:

- OCI registry
- Juju controller name + model name
- Kubernetes context

### 1. Push the rock

```bash
rockcraft.skopeo copy --insecure-policy \
  oci-archive:masterclasses-canonical-com_0.1_amd64.rock \
  docker://<registry>/masterclasses-canonical-com:0.1
```

### 2. Deploy the charm

```bash
# Add the Kubernetes cloud and create a model if not already done
juju add-k8s <cloud-name> --controller <controller>
juju add-model <model> <cloud-name>

# Deploy
juju deploy ./charm/masterclasses-canonical-com_amd64.charm \
  --resource flask-app-image=<registry>/masterclasses-canonical-com:0.1

# Integrate postgresql (e.g. using the postgresql-k8s charm)
juju integrate masterclasses-canonical-com postgresql-k8s

# Configure required options
juju config masterclasses-canonical-com flask-secret-key=secret:<secret-uri>
juju config masterclasses-canonical-com openid-launchpad-team=<team>
# ... set remaining config options as needed
```

Handoff payload: `.agents/12factor-handoff.yaml`
