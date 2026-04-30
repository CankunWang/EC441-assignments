#!/usr/bin/env python3
"""minimap - a tiny nmap-like async TCP port scanner."""

import argparse
import asyncio
import hashlib
import ipaddress
import re
import ssl
import sys
from collections import defaultdict

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    _HAVE_CRYPTO = True
except ImportError:
    _HAVE_CRYPTO = False

# Nmap's top-100 TCP ports by frequency (from nmap-services).
TOP_100_PORTS = [
    7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 88, 106, 110, 111,
    113, 119, 135, 139, 143, 144, 179, 199, 389, 427, 443, 444, 445, 465,
    513, 514, 515, 543, 544, 548, 554, 587, 631, 646, 873, 990, 993, 995,
    1025, 1026, 1027, 1028, 1029, 1110, 1433, 1720, 1723, 1755, 1900,
    2000, 2001, 2049, 2121, 2717, 3000, 3128, 3306, 3389, 3986, 4899,
    5000, 5009, 5051, 5060, 5101, 5190, 5357, 5432, 5631, 5666, 5800,
    5900, 6000, 6001, 6646, 7070, 8000, 8008, 8009, 8080, 8081, 8443,
    8888, 9100, 9999, 10000, 32768, 49152, 49153, 49154, 49155, 49156,
    49157,
]

# Common port -> service name. Anything else is reported as "unknown".
PORT_SERVICES = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "domain",
    80: "http", 110: "pop3", 111: "rpcbind", 135: "msrpc", 139: "netbios-ssn",
    143: "imap", 179: "bgp", 389: "ldap", 443: "https", 445: "microsoft-ds",
    465: "smtps", 587: "submission", 631: "ipp", 873: "rsync", 993: "imaps",
    995: "pop3s", 1433: "ms-sql", 1723: "pptp", 3306: "mysql",
    3389: "ms-wbt-server", 5432: "postgresql", 5900: "vnc", 6379: "redis",
    8000: "http-alt", 8080: "http-proxy", 8443: "https-alt", 8888: "http-alt",
    9100: "jetdirect", 27017: "mongodb",
}

# Banner signatures: (compiled regex, service name, format string).
# Format string uses regex named groups. Missing groups become empty.
_SIG_RAW = [
    # SSH banner per RFC 4253: "SSH-protoversion-softwareversion[ comments]"
    (r"^SSH-(?P<proto>\d+\.\d+)-(?P<product>\S+)(?:\s+(?P<extra>[^\r\n|]+))?",
     "ssh", "{product} {extra} (proto {proto})"),
    # HTTP Server response header
    (r"Server:\s*(?P<product>[^\r\n|]+)",
     "http", "{product}"),
    # FTP greeting (vsFTPd, ProFTPD, Pure-FTPd, FileZilla, generic)
    (r"^220[- ].*?\b(?P<product>vsFTPd|ProFTPD|FileZilla|Pure-FTPd|Microsoft FTP)\b\s*v?(?P<version>[\d.]+)?",
     "ftp", "{product} {version}"),
    # SMTP/ESMTP greeting
    (r"^220[- ].*?\b(?P<product>Postfix|Exim|Sendmail|Microsoft|Exchange)\b",
     "smtp", "{product}"),
    # POP3 greeting
    (r"^\+OK.*?\b(?P<product>Dovecot|UW POP3|Cyrus|Microsoft Exchange)\b",
     "pop3", "{product}"),
    # IMAP greeting
    (r"^\* OK.*?\b(?P<product>Dovecot|Cyrus|Courier|Microsoft Exchange)\b",
     "imap", "{product}"),
    # Telnet login banner (loose hint at the OS/vendor)
    (r"\b(?P<product>Cisco|Linux|Ubuntu|Debian|FreeBSD|OpenBSD|HP-UX)\b.*login:",
     "telnet", "{product}"),
]

SIGNATURES = [
    (re.compile(p, re.IGNORECASE | re.MULTILINE), s, f) for p, s, f in _SIG_RAW
]


def identify_service(port, banner):
    """Return (service_name, version_string_or_None) for a port and its banner."""
    base = PORT_SERVICES.get(port, "unknown")
    if not banner:
        return base, None
    for regex, service, fmt in SIGNATURES:
        m = regex.search(banner)
        if not m:
            continue
        groups = defaultdict(str, {k: (v or "") for k, v in m.groupdict().items()})
        version = fmt.format_map(groups)
        # Clean empty placeholders like "(proto )" or stray double spaces.
        version = re.sub(r"\(\s*proto\s*\)", "", version)
        version = re.sub(r"\s+", " ", version).strip()
        return service, version or None
    return base, None


# Ports where we can safely send a plaintext probe to elicit a banner.
HTTP_PROBE_PORTS = {80, 81, 8000, 8008, 8080, 8081, 8888, 3000, 5000, 8009}

# Ports that speak TLS first; sending plaintext just hangs.
TLS_PORTS = {443, 444, 465, 636, 993, 995, 8443}


async def grab_tls_info(host, port, timeout):
    """Open a TLS connection and pull TLS version, cipher, and cert metadata.

    Uses CERT_NONE so expired / self-signed / hostname-mismatched certs still
    return their info — we want to *report* what's there, not validate it.
    Returns a dict with keys: version, cipher, cipher_bits, subject, issuer,
    not_before, not_after. Returns None on handshake failure.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ctx, server_hostname=host),
            timeout=timeout,
        )
    except (asyncio.TimeoutError, ssl.SSLError, ConnectionResetError, OSError):
        return None

    info = {}
    try:
        ssl_obj = writer.get_extra_info("ssl_object")
        if ssl_obj is None:
            return None
        info["version"] = ssl_obj.version() or "unknown"
        cipher = ssl_obj.cipher()
        if cipher:
            info["cipher"] = cipher[0]
            info["cipher_bits"] = cipher[2]

        cert_der = ssl_obj.getpeercert(binary_form=True)
        if cert_der:
            # SHA-256 fingerprint of the leaf cert (no parsing needed).
            digest = hashlib.sha256(cert_der).hexdigest().upper()
            info["sha256"] = ":".join(digest[i:i + 2] for i in range(0, 64, 2))

        if cert_der and _HAVE_CRYPTO:
            try:
                cert = x509.load_der_x509_certificate(cert_der, default_backend())
                cn = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
                info["subject"] = cn[0].value if cn else cert.subject.rfc4514_string()
                cn = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
                info["issuer"] = cn[0].value if cn else cert.issuer.rfc4514_string()
                # cryptography >= 42 prefers the *_utc variants
                try:
                    nb = cert.not_valid_before_utc
                    na = cert.not_valid_after_utc
                except AttributeError:
                    nb = cert.not_valid_before
                    na = cert.not_valid_after
                info["not_before"] = nb.strftime("%Y-%m-%d")
                info["not_after"] = na.strftime("%Y-%m-%d")

                # Subject Alternative Names (modern browsers prefer these over CN).
                try:
                    san_ext = cert.extensions.get_extension_for_oid(
                        x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                    )
                    dns_names = [
                        n.value for n in san_ext.value
                        if isinstance(n, x509.DNSName)
                    ]
                    if dns_names:
                        info["san"] = dns_names
                except x509.ExtensionNotFound:
                    pass
            except Exception:
                pass

    finally:
        try:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), timeout=0.5)
        except Exception:
            pass

    return info or None


async def scan_port(host, port, timeout):
    """Try TCP connect; on success grab banner and (for TLS ports) TLS metadata.

    Returns (port, state, banner, tls_info).
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
    except asyncio.TimeoutError:
        return port, "filtered", None, None
    except (ConnectionRefusedError, OSError):
        return port, "closed", None, None

    banner = None
    if port not in TLS_PORTS:
        try:
            if port in HTTP_PROBE_PORTS:
                writer.write(b"HEAD / HTTP/1.0\r\nHost: scan\r\n\r\n")
                try:
                    await asyncio.wait_for(writer.drain(), timeout=1.0)
                except asyncio.TimeoutError:
                    pass
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=1.5)
                if data:
                    banner = data.decode("latin-1", errors="replace")
                    banner = banner.replace("\r", "").replace("\n", " | ").strip()
                    if len(banner) > 256:
                        banner = banner[:253] + "..."
            except asyncio.TimeoutError:
                pass
        except Exception:
            pass

    try:
        writer.close()
        await asyncio.wait_for(writer.wait_closed(), timeout=0.5)
    except Exception:
        pass

    tls_info = None
    if port in TLS_PORTS:
        tls_info = await grab_tls_info(host, port, timeout)

    return port, "open", banner, tls_info


async def tcp_ping(host, timeout=1.0):
    """Cheap host-up check: try a handful of common ports."""
    for p in (80, 443, 22, 445, 3389):
        try:
            _, w = await asyncio.wait_for(
                asyncio.open_connection(host, p), timeout=timeout
            )
            w.close()
            try:
                await asyncio.wait_for(w.wait_closed(), timeout=0.5)
            except Exception:
                pass
            return True
        except Exception:
            continue
    return False


async def scan_host(host, ports, timeout, concurrency):
    sem = asyncio.Semaphore(concurrency)

    async def bounded(p):
        async with sem:
            return await scan_port(host, p, timeout)

    results = await asyncio.gather(*(bounded(p) for p in ports))
    open_ports = sorted([r for r in results if r[1] == "open"])

    print(f"\nScan report for {host}")
    if not open_ports:
        print(f"  All {len(ports)} scanned ports are closed or filtered.")
        return

    print(f"  {'PORT':<8}{'STATE':<10}{'SERVICE':<14}VERSION / BANNER")
    print(f"  {'-'*8}{'-'*10}{'-'*14}{'-'*60}")
    indent = " " * 14  # under SERVICE column for sub-detail rows

    for port, state, banner, tls_info in open_ports:
        service, version = identify_service(port, banner)
        if tls_info:
            v = tls_info.get("version", "TLS")
            cipher = tls_info.get("cipher", "")
            info = f"{v} / {cipher}" if cipher else v
        else:
            info = version if version else (banner or "")
        if len(info) > 70:
            info = info[:67] + "..."
        print(f"  {port:<8}{state:<10}{service:<14}{info}")

        if tls_info:
            bits = tls_info.get("cipher_bits")
            if bits:
                print(f"  {indent}|- cipher bits: {bits}")
            subj = tls_info.get("subject")
            if subj:
                print(f"  {indent}|- subject:     {subj}")
            sans = tls_info.get("san")
            if sans:
                shown = ", ".join(sans[:5])
                more = f" (+{len(sans) - 5} more)" if len(sans) > 5 else ""
                print(f"  {indent}|- SAN:         {shown}{more}")
            issuer = tls_info.get("issuer")
            if issuer:
                print(f"  {indent}|- issuer:      {issuer}")
            nb = tls_info.get("not_before")
            na = tls_info.get("not_after")
            if nb and na:
                print(f"  {indent}|- valid:       {nb} -> {na}")
            sha = tls_info.get("sha256")
            if sha:
                # SHA-256 hex is 95 chars with colons; wrap onto two lines.
                print(f"  {indent}|- SHA-256:     {sha[:47]}")
                print(f"  {indent}               {sha[48:]}")


def parse_ports(spec):
    """Parse '1-1000' or '22,80,443-445' into a sorted list of ports."""
    ports = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            ports.update(range(int(a), int(b) + 1))
        else:
            ports.add(int(part))
    return sorted(p for p in ports if 1 <= p <= 65535)


def expand_targets(target):
    """Accept single host, IP, or CIDR. Returns a list of target strings."""
    try:
        net = ipaddress.ip_network(target, strict=False)
        if net.num_addresses == 1:
            return [str(net.network_address)]
        return [str(ip) for ip in net.hosts()]
    except ValueError:
        return [target]


async def main():
    ap = argparse.ArgumentParser(
        description="minimap - tiny async TCP port scanner",
    )
    ap.add_argument("target", help="hostname, IP, or CIDR (e.g. 192.168.1.0/24)")
    ap.add_argument("-p", "--ports",
                    help="port spec, e.g. 1-1000 or 22,80,443. Overrides --top.")
    ap.add_argument("--top", type=int, default=100,
                    help="scan top N common ports (default 100, max 100)")
    ap.add_argument("-t", "--timeout", type=float, default=1.5,
                    help="connect timeout in seconds (default 1.5)")
    ap.add_argument("-c", "--concurrency", type=int, default=200,
                    help="max concurrent sockets (default 200)")
    ap.add_argument("--no-ping", action="store_true",
                    help="skip host-up check on multi-target scans")
    args = ap.parse_args()

    if args.ports:
        ports = parse_ports(args.ports)
    else:
        n = max(1, min(args.top, len(TOP_100_PORTS)))
        ports = sorted(TOP_100_PORTS[:n])

    targets = expand_targets(args.target)
    print(f"minimap: {len(targets)} target(s), {len(ports)} ports each, "
          f"timeout={args.timeout}s, concurrency={args.concurrency}")

    for t in targets:
        if not args.no_ping and len(targets) > 1:
            up = await tcp_ping(t)
            if not up:
                print(f"\n{t}: host appears down (use --no-ping to force scan)")
                continue
        await scan_host(t, ports, args.timeout, args.concurrency)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
