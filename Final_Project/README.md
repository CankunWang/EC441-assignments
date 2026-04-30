# minimap

A small async TCP port scanner with banner-based service version detection and TLS metadata extraction. Written as the EC 441 (Spring 2026) final project.

About 320 lines of Python in a single file. Goal: build a working subset of `nmap` that demonstrates the post-midterm tools/sockets material, plus the new application-layer and cryptography content from L23 and L24.

## What it does

- Async TCP connect scan, with concurrency control
- Built-in nmap top-100 port list, plus arbitrary `-p` ranges
- Hostname / single IP / CIDR (`192.168.1.0/24`) targets
- Banner grabbing on open ports (HTTP `HEAD` probe + passive read for others)
- 7 banner regex signatures to extract product + version: SSH, HTTP, FTP, SMTP, POP3, IMAP, Telnet
- TLS handshake on TLS ports (443, 993, 995, 8443, ...) and reports:
  - TLS version (e.g. TLSv1.2, TLSv1.3)
  - Cipher suite + key bits
  - Certificate subject CN
  - Certificate issuer CN
  - Validity period

## Requirements

- Python 3.10 or newer
- `cryptography` for X.509 parsing

```
pip install cryptography
```

No other third-party dependencies. Tested on Windows 11 + Python 3.11.

## Quick start

```
python minimap.py 127.0.0.1
python minimap.py scanme.nmap.org
python minimap.py nmap.org -p 22,80,443
```

## Usage

```
python minimap.py <target> [options]
```

| Flag | Meaning | Default |
|---|---|---|
| `target` | host, IP, or CIDR (positional, required) | — |
| `-p, --ports` | port spec, e.g. `1-1000` or `22,80,443-445` | — |
| `--top N` | scan the top N common ports | 100 |
| `-t, --timeout` | per-port connect timeout in seconds | 1.5 |
| `-c, --concurrency` | max concurrent sockets in flight | 200 |
| `--no-ping` | skip the TCP-ping host-up check | off |

When `-p` is given it overrides `--top`.

### Examples

Scan localhost with a small custom port set:
```
python minimap.py 127.0.0.1 -p 80,135,139,443,445,3389
```

Scan top-100 ports of the public test target:
```
python minimap.py scanme.nmap.org
```

Scan a class C subnet with a small port set:
```
python minimap.py 192.168.1.0/24 --top 20
```

Pull TLS metadata from a real HTTPS server:
```
python minimap.py nmap.org -p 443
```

## Output

```
$ python minimap.py nmap.org -p 22,80,443

minimap: 1 target(s), 3 ports each, timeout=1.5s, concurrency=200

Scan report for nmap.org
  PORT    STATE     SERVICE       VERSION / BANNER
  --------------------------------------------------------------------------------------------
  80      open      http          Apache/2.4.6 (CentOS)
  443     open      https         TLSv1.2 / ECDHE-RSA-AES128-GCM-SHA256
                |- cipher bits: 128
                |- subject:     insecure.com
                |- issuer:      R13
                |- valid:       2026-03-22 -> 2026-06-20
```

Closed and filtered ports are not printed; only `open` rows show up.

## How it works

### TCP connect scan

`asyncio.open_connection(host, port)` is used as the probe. A `Semaphore` bounds concurrent in-flight sockets (default 200). Each port resolves to one of three states:

- **open** — `open_connection` returned, meaning the kernel completed the full TCP three-way handshake
- **closed** — the peer responded with a TCP RST (`ConnectionRefusedError`)
- **filtered** — the connect timed out, suggesting a firewall is dropping packets silently

This is the same probe model as `nmap -sT`. SYN scan (`nmap -sS`) was deliberately not implemented — it requires raw sockets, which on Windows means installing Npcap and running with elevated privileges.

### Host discovery

When the target list has more than one host (i.e. a CIDR was given), each host is first checked with a "TCP ping" — a quick connect attempt against a few common ports (80, 443, 22, 445, 3389) with a short timeout. Hosts that don't respond on any of these are skipped. `--no-ping` disables this so every IP in the range is scanned.

### Banner grabbing

For HTTP-style ports (80, 8080, 8000, ...), the scanner sends `HEAD / HTTP/1.0` to elicit a response from the server. For TLS ports, the plaintext probe is skipped (would hang waiting for ClientHello). For everything else, a 1.5-second passive read picks up servers that send a banner on connect (SSH, SMTP, FTP, POP3, IMAP).

Raw banners are normalized (`\r\n` → ` | `) and stored up to 256 bytes for regex matching. Display is truncated to 70 chars.

### Service identification

Two layers:

1. **Port lookup.** A small dict of 35 well-known ports → service names. This is what `nmap` does in default mode (no `-sV`).
2. **Banner regex.** 7 patterns parse banners into a structured product + version string. SSH follows RFC 4253 (`SSH-protoversion-softwareversion comments`) and is very reliable. HTTP uses the `Server:` response header. FTP / SMTP / POP3 / IMAP all have well-known greeting formats.

Services that don't volunteer a banner without a protocol-specific probe (PostgreSQL, MySQL with auth, Memcached, Redis without `PING`, etc.) get the port-based service name but no version. Building the full nmap-service-probes engine (~12,000 signatures, 30+ probes) was out of scope.

### TLS metadata

For TLS ports, after the plain TCP probe finishes, a second connection is opened with TLS:

```python
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode    = ssl.CERT_NONE
reader, writer = await asyncio.open_connection(
    host, port, ssl=ctx, server_hostname=host
)
```

`CERT_NONE` is intentional. A scanner should **report** the certificate it sees, not refuse to talk to expired or self-signed servers. After the handshake completes, the TLS object exposes:

- `version()` → `'TLSv1.3'`
- `cipher()` → `('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)`
- `getpeercert(binary_form=True)` → DER bytes

The DER cert is decoded with the `cryptography` library to extract the subject and issuer Common Names plus the `notBefore` / `notAfter` timestamps.

To prove this is "report, not validate": scanning `expired.badssl.com` returns the cert metadata cleanly and shows `valid: 2015-04-09 -> 2015-04-12`. The dates are obviously in the past; the scanner does not crash, hide them, or substitute a fake-OK status.

## Course content covered

| Lecture / topic | Where it appears |
|---|---|
| L18 TCP three-way handshake | every successful connect = a full handshake |
| L21–L22 Tools / sockets | core architecture (asyncio + `socket` + `ssl`) |
| L13–L17 Network layer | CIDR parsing and multi-host scanning |
| L23 Application layer | banner grabbing + per-protocol signature parsing |
| L24 Cryptography / TLS | TLS handshake, cipher suite reporting, X.509 extraction |

## What it does not do

Out of scope by design — these were considered and ruled out for time / platform reasons:

- **SYN scan / UDP scan / ICMP ping** — need raw sockets, which need Npcap on Windows
- **OS fingerprinting** — needs analysis of TCP/IP stack quirks
- **Full nmap-service-probes** — would need the probe engine and signature DB
- **Scapy integration** — same Npcap reason
- **Mininet experiments** — would need a WSL2 environment
- **Concurrent multi-host scanning** — hosts are scanned sequentially; ports inside one host run concurrently

## Files

```
Final_Project/
  minimap.py    # the scanner
  README.md     # this file
```

## Legal / ethical

Only scan targets you are authorized to scan. During development and the demo I used:

- `127.0.0.1` — localhost
- `scanme.nmap.org` — the Nmap project's official test target, scanning explicitly permitted
- `nmap.org`, `expired.badssl.com` — public servers, single-port queries to demonstrate TLS metadata
- My own home WiFi subnet

Do **not** scan:

- BU campus network addresses you don't own
- Other people's machines on shared networks
- Random public IP space

Unauthorized scanning can violate the U.S. Computer Fraud and Abuse Act, BU's acceptable use policy, and similar rules in other jurisdictions.

