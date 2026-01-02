# Docker Compose Infrastructure Design

## Overview

Extract Garage (S3 cache) and Registry from Python-managed containers into a Docker Compose setup, adding a registry UI. This provides a more real-world infrastructure setup that works for both local development and CI.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   docker-compose.yml                     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    garage    │  │   registry   │  │  registry-ui │  │
│  │  (S3 cache)  │  │ (registry:2) │  │   (joxit)    │  │
│  │  :3900-3903  │  │    :5050     │  │    :5051     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
└────────────────────────────┼────────────────────────────┘
                             │
                    image-manager CLI
                    (connects to services)
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Service lifecycle | Compose-only | Clean separation - compose owns lifecycle, Python connects |
| Registry UI | joxit/docker-registry-ui | Simple, lightweight, read-only |
| Python management code | Remove | Services must be running via compose |
| Garage credentials | Fixed/hardcoded | Simpler, sufficient for local dev/CI |
| Ports | Keep existing | No code changes for connection logic |
| Registry UI port | 5051 | Next to registry (5050) |
| start/stop/status CLI | Keep for buildkitd/dind only | These are still Python-managed |

## Docker Compose Configuration

### docker-compose.yml

```yaml
services:
  garage:
    image: dxflrs/garage:v2.1.0
    ports:
      - "127.0.0.1:3900:3900"  # S3 API
      - "127.0.0.1:3901:3901"  # RPC
      - "127.0.0.1:3903:3903"  # Admin
    volumes:
      - garage-meta:/var/lib/garage/meta
      - garage-data:/var/lib/garage/data
      - ./infrastructure/garage.toml:/etc/garage.toml:ro

  registry:
    image: registry:2
    ports:
      - "127.0.0.1:5050:5000"
    volumes:
      - registry-data:/var/lib/registry

  registry-ui:
    image: joxit/docker-registry-ui:latest
    ports:
      - "127.0.0.1:5051:80"
    environment:
      - REGISTRY_TITLE=Image Manager Registry
      - REGISTRY_URL=http://registry:5000
    depends_on:
      - registry

volumes:
  garage-meta:
  garage-data:
  registry-data:
```

### infrastructure/garage.toml

Static configuration with fixed credentials:

```toml
metadata_dir = "/var/lib/garage/meta"
data_dir = "/var/lib/garage/data"
db_engine = "lmdb"
replication_factor = 1

[rpc]
rpc_bind_addr = "[::]:3901"
rpc_public_addr = "127.0.0.1:3901"
rpc_secret = "<fixed 64-char hex>"

[s3_api]
api_bind_addr = "[::]:3900"
s3_region = "garage"

[admin]
api_bind_addr = "0.0.0.0:3903"
admin_token = "<fixed token>"
```

### infrastructure/garage-init.sh

Initialization script that:
1. Waits for garage to be healthy
2. Configures node layout (if not already done)
3. Creates `buildkit-cache` bucket
4. Creates access key with fixed ID/secret

Runs via `docker compose run --rm garage-init` or as sidecar container.

## Python Code Changes

### Remove from manager/building.py

**Registry management:**
- `start_registry()`
- `stop_registry()`
- `is_registry_running()`
- `ensure_registry()`

**Garage management:**
- `start_garage()`
- `stop_garage()`
- `is_garage_running()`
- `ensure_garage()`
- `generate_garage_config()`
- `_initialize_garage_cluster()`
- `get_garage_config_dir()`
- `get_garage_credentials_file()`
- `get_garage_credentials()`
- `save_garage_credentials()`

### Keep (with modifications)

**Unchanged:**
- `get_registry_addr()`
- `get_registry_addr_for_buildkit()`
- `get_garage_s3_endpoint()`
- `get_garage_s3_endpoint_for_buildkit()`
- Port constants

**New credentials approach:**
- Hardcode fixed access key ID and secret in constants
- Remove file-based credential storage

**Remove `auto_start` parameter from:**
- `build_image()`
- `create_manifest()`
- `create_manifest_from_registry()`

Functions assume services are running; fail with clear error if not reachable.

## CLI Changes

### manager/__main__.py

**Keep start/stop/status for:**
- `buildkitd`
- `dind`

**Remove from start/stop/status:**
- `registry`
- `garage`
- `all` option (or redefine to mean buildkitd+dind)

## Error Handling

When registry or garage is unreachable:

```
Error: Registry not reachable at localhost:5050
Run 'docker compose up -d' to start infrastructure services.
```

## File Structure

```
├── docker-compose.yml
├── infrastructure/
│   ├── garage.toml
│   └── garage-init.sh
├── manager/
│   ├── building.py  (simplified)
│   └── __main__.py  (updated CLI)
```

## Usage

### Quick Start

```bash
# Start infrastructure
docker compose up -d

# Open registry UI
open http://localhost:5051

# Build images
uv run image-manager build base:2025.09
```

### Teardown

```bash
docker compose down        # Stop services, keep data
docker compose down -v     # Stop services, delete data
```
