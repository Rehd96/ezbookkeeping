# VPS outage & debug session — 2026-08-29

Deploying the `feature/budget-tracking` fork (grocery-grouping change to the Weekly Spending
Breakdown card) triggered a cascading failure on the IONOS VPS. This is the full chain of
issues and fixes, in order.

## Environment

- IONOS VPS, Ubuntu, hostname `ubuntu`, ~3.8 GB RAM, `/dev/vda1` 117 GB.
- Public IP `217.154.23.127`, gateway `217.154.23.1`, primary NIC `ens6` (virtio, DHCP).
- Reached over **Tailscale** only — public port 22 is firewalled by IONOS.
- Runs several Docker stacks: `festival-*` (web/api/postgres/redis/monitor), `donetick`,
  and `ezbookkeeping`.
- Public domain is **labustagialla.it** (host nginx, systemd service, reverse-proxies to the
  container on `127.0.0.1:8080`). NOT "labustiagialla.it" — easy to misspell.

## Timeline of issues

### 1. Frontend build failed — `vue-tsc` OOM

```
FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory
Error: Failed to pass lint checking
Dockerfile:37  RUN ./build.sh frontend
```

**Cause:** `vue-tsc` type-check needs >2 GB; VPS Node heap capped at ~1.9 GB.
**Fix:** build with `--build-arg NO_LINT=1` (Dockerfile already has the `NO_LINT` ARG/ENV;
`build.sh` honours it). Lint/type-check is done on the dev machine instead. Local `vue-tsc`
on the change passed clean.

### 2. Build extremely slow / appeared stuck (800–1000 s)

**Causes (compounding):**
- Docker **build cache had grown to 60.94 GB** (49.38 GB reclaimable) on a disk at 80 % full.
- Transient **systemd-resolved DNS failures** (`degraded feature set UDP instead of UDP+EDNS0`,
  "grace period" flapping) stalled `npm install` for minutes at a time.
- Building Go backend **and** bundling the two Vite SPAs concurrently on 2 vCPU while the other
  stacks ran.

**Fixes:**
- `docker builder prune -f` → reclaimed **49.38 GB** (disk 93 G → 41 G used).
- Recommend capping cache permanently via `/etc/docker/daemon.json`:
  `{"builder":{"gc":{"enabled":true,"defaultKeepStorage":"10GB"}}}` then `systemctl restart docker`.
- Optional weekly `docker-prune.timer` (systemd) running
  `docker system prune -af --filter until=168h` + `docker builder prune -af --filter until=168h`.

### 3. Build exhausted all memory — box unresponsive, SSH dead

```
free -m →  Mem 3633/3859 used,  Swap 2047/2047 used,  available 40 MB
docker stats  → hung
```

**Cause:** concurrent Go + Vite builds ate all RAM + all 2 GB swap → thrashing; `sshd` could
not fork sessions.
**Fix:**
```
fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
pkill -9 -f build.sh ; pkill -9 -f 'go build' ; pkill -9 -f buildkitd
systemctl restart docker
```
RAM recovered to ~1.9 GB free. Swap made permanent in `/etc/fstab`.
**Lesson: never build this image on the VPS — build locally, ship the image.**

### 4. `labustagialla.it` "unreachable" — was a typo

Testing `labustiagialla.it` (extra `i`). The real domain `labustagialla.it` was serving
`200 OK` the whole time; the live container never went down. nginx logs showed
`server: labustagialla.it`. Also confirmed public port 22 times out (IONOS firewall) — the
box is reachable only via Tailscale.

### 5. SSH still down after RAM recovered — Tailscale offline

`sshd` was `active (running)` the whole time. `tailscale status` showed the VPS itself as
`offline` with:
```
Unable to connect to the Tailscale coordination server to synchronize the state of your tailnet.
tailscaled: ... failed to resolve "controlplane.tailscale.com": no DNS fallback candidates remain
```
**Cause:** DNS resolution was broken (knock-on from step 3 / systemd-resolved), so `tailscaled`
could not reach `controlplane.tailscale.com`.

### 6. DNS completely broken

```
resolvectl query controlplane.tailscale.com
  → resolve call failed: No appropriate name servers or networks for name found
/etc/resolv.conf  → did not exist
```

**Fixes applied:**
```
systemctl stop systemd-resolved
systemctl disable systemd-resolved
printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' > /etc/resolv.conf   # NOTE: resolv, not "resolve"
```
`nsswitch.conf` already `hosts: files dns` (good). Static resolv.conf is stable and survives
reboot now that resolved is disabled.

### 7. Root cause revealed — no network at all

```
ping -c2 1.1.1.1  → connect: Network is unreachable
ip route          → only docker bridge routes, NO default route
ip -brief addr    → ens6 UP but only a link-local fe80:: address, NO IPv4
```

**Cause:** the primary interface lost its DHCP lease / address; `systemd-networkd` state
collapsed during the OOM. netplan config itself was intact (cloud-init generated,
`dhcp4: true` match `en*`, renderer networkd).

**Fix that worked:**
```
systemctl restart systemd-networkd
networkctl reconfigure ens6
```
`ens6` came back: `routable (configured)`, `online`, Address `217.154.23.127/32`,
Gateway `217.154.23.1`, default route restored, DNS working.

### 8. Recovery

```
systemctl restart tailscaled && tailscale up   → VPS back online, SSH from laptop works
docker ps                                       → all stacks Up
```

## Post-recovery findings

- **Two ezbookkeeping containers exist:**
  - `ezbookkeeping` — image **`ezbookkeeping:budget`** — the LIVE container on `:8080`.
  - `ezbookkeeping-old` — image `mayswind/ezbookkeeping` — crash-looping leftover; removed with
    `docker rm -f ezbookkeeping-old`.
- The real deploy image tag is **`ezbookkeeping:budget`**, NOT `mayswind/ezbookkeeping`.
  `/root/docker-compose.yml` (which references `mayswind/ezbookkeeping`) is not the compose file
  that owns the live container. Find the real one with:
  `docker inspect ezbookkeeping --format '{{ index .Config.Labels "com.docker.compose.project.config_files"}}'`

## Backend build fails on `TestExchangeRatesApiLatestExchangeRateHandler_*`

`./build.sh backend` runs `go test ./... -v`, which includes tests that call **live
third-party central-bank APIs** (e.g. `TestExchangeRatesApiLatestExchangeRateHandler_NationalBankOfRomaniaDataSource`).
These are self-skipped only when `BUILD_PIPELINE=1` (and `CHECK_3RD_API != 1`) — which is what
upstream CI sets. If the external endpoint is down/blocked, the build fails with
`failed to request third party api` even though nothing is wrong with the code.

**Fix:** always pass `--build-arg BUILD_PIPELINE=1` (the Dockerfile already wires the ARG/ENV).
This skips only the live-API tests, not real unit tests.

## Correct deploy procedure (going forward)

1. On the **dev machine**, in `~/ezbookkeeping` on `feature/budget-tracking`:
   ```
   docker build --build-arg NO_LINT=1 --build-arg BUILD_PIPELINE=1 -t ezbookkeeping:budget .
   docker save ezbookkeeping:budget | gzip | ssh root@217.154.23.127 'gunzip | docker load'
   ```
2. On the VPS, from the directory of the real compose file:
   ```
   docker compose up -d ezbookkeeping
   docker inspect ezbookkeeping --format '{{.Created}}'
   ```
3. Never `docker build` on the VPS. Never `docker compose pull` the ezbookkeeping service
   (would replace the fork with upstream).

## Hardening checklist (still TODO)

- [ ] `/etc/docker/daemon.json` builder GC cap (10 GB).
- [ ] Keep the 4 GB `/swapfile` (in `/etc/fstab`).
- [ ] IONOS firewall: allow inbound TCP 22 from home IP as a Tailscale-independent fallback.
- [ ] Decide: keep systemd-resolved disabled + static resolv.conf (simple, done), or re-enable
      and add explicit `nameservers:` to netplan.
- [ ] `systemctl enable tailscaled` so Tailscale auto-starts on boot (see below).
- [ ] Confirm every container has `restart: unless-stopped`.
