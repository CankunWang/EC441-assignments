# Week 11 - DNS, HTTP Versions, and QUIC

This week I picked the parts of Lecture 23 that Week 10 did not cover: DNS, the difference between HTTP/1.1, HTTP/2, and HTTP/3, and QUIC.

## Problem

### 1. DNS resolution chain

A laptop wants `www.eng.bu.edu`. The recursive resolver's cache is empty.

1. List the servers contacted in order, from the laptop down to the final answer.
2. Which step is recursive and which steps are iterative?
3. Why does the laptop normally never talk to a root server?
4. The same laptop reloads 1 minute later, with TTL = 3600s. Which steps are skipped?
5. A second laptop on the same network asks for `mail.eng.bu.edu` 30 seconds later. Which cached records help?

### 2. Records and TTL

```
example.com.       3600  IN  SOA   ns1.example.com. admin.example.com. (...)
example.com.       3600  IN  NS    ns1.example.com.
example.com.       3600  IN  NS    ns2.example.com.
example.com.       3600  IN  MX    10 mail.example.com.
example.com.       3600  IN  MX    20 backup.example.com.
example.com.       3600  IN  A     192.0.2.10
www.example.com.   3600  IN  CNAME example.com.
mail.example.com.  3600  IN  A     192.0.2.20
example.com.       3600  IN  TXT   "v=spf1 mx -all"
```

1. Mail to `alice@example.com`: which server is tried first, which is the backup?
2. What does `www.example.com` resolve to as a final IPv4 address?
3. Why two `NS` records?
4. The internet sends `10^12` DNS queries per day. If 99.9% are answered from caches, how many queries per second hit authoritative servers?
5. The admin lowers TTL to 60s before a planned IP change. What is the cost, and why is it still worth it?

### 3. DNS transport

1. Why is UDP/53 the default rather than TCP/53?
2. When does DNS fall back to TCP/53?
3. DoT uses port 853, DoH uses port 443. Why is DoH harder to block?
4. Give one reason a school network might dislike DoH.

### 4. HTTP/1.1 vs HTTP/2 vs HTTP/3 page load

A page is 1 HTML document plus 30 sub-resources. The HTML takes 200 ms. 29 sub-resources take 50 ms each, and 1 slow resource takes 2000 ms. Bandwidth is plentiful.

1. Estimate the load time over HTTP/1.1 with 6 parallel TCP connections, no pipelining.
2. Estimate the load time over HTTP/2, single TCP connection, no loss.
3. One TCP segment in the slow transfer is lost and takes one extra 80 ms RTT to recover. What does this do to the other 29 streams in HTTP/2? In HTTP/3?
4. Difference between application-level HOL and TCP-level HOL?
5. In HTTP/2, what do `:method`, `:path`, and `:authority` correspond to in HTTP/1.1?

### 5. QUIC handshake and design

Use `RTT = 80 ms` for parts 1-2.

1. Fresh TCP + TLS 1.3 needs about 2 RTT before the first HTTP byte. Fresh QUIC needs 1 RTT. Resumed QUIC with 0-RTT needs 0.5 RTT. Compute the time to first byte for each.
2. How many ms does QUIC 0-RTT save vs TCP + TLS 1.3 on a fresh load?
3. Why is QUIC built on UDP instead of as a new L4 protocol?
4. What does "QUIC moves transport into user space" mean? Why does that make it easier to evolve than TCP?
5. Give one realistic case where QUIC connection migration matters and TCP would have to start over.

---

## Solution

### 1. DNS resolution chain

The laptop's stub resolver sends the query to a recursive resolver (`1.1.1.1`, `8.8.8.8`, or the ISP's). The resolver does the rest:

1. laptop -> recursive resolver
2. resolver -> root server, asks about `edu`
3. resolver -> `edu` TLD server, asks about `bu.edu`
4. resolver -> `bu.edu` authoritative server, asks about `eng.bu.edu`
5. resolver -> `eng.bu.edu` authoritative server, asks for the A record of `www.eng.bu.edu`
6. resolver -> laptop, with the answer

The laptop's request is recursive ("give me the final answer"). The resolver's queries are iterative: each authoritative server answers with what it knows or with a referral.

The laptop does not talk to root because root is shared by the whole internet. If every laptop went there directly, root would not scale. Recursive resolvers absorb load by caching.

On reload after 1 minute, the resolver still has the answer cached, so steps 2-5 are skipped. The stub may also cache locally and skip step 1.

For `mail.eng.bu.edu` 30 seconds later, the cached `NS` records for `edu`, `bu.edu`, and `eng.bu.edu` still apply. The resolver jumps straight to the `eng.bu.edu` authoritative server. Only the final A lookup is new.

### 2. Records and TTL

`alice@example.com` follows the `MX` records. Lower priority wins, so `mail.example.com` (10) is tried first, `backup.example.com` (20) is the fallback.

`www.example.com` is a CNAME for `example.com`, which has A `192.0.2.10`. So `www.example.com` -> `192.0.2.10`.

Two `NS` records give redundancy. If one server is down, the other still answers, and resolvers can pick the closer one.

Rate calculation:

```
total per day        = 10^12
to authoritative     = 10^12 * 0.001 = 10^9
seconds in a day     = 86400
to authoritative/sec = 10^9 / 86400 ~= 1.16 * 10^4
```

So about 12,000 queries per second hit authoritative servers, while the system as a whole is doing ~1.16 * 10^7 per second. Caching cuts the load by 1000x.

Lowering TTL to 60s costs more authoritative traffic and slightly higher lookup latency. The benefit is that DNS converges in about a minute when the IP changes, instead of an hour. For a planned migration this is the right tradeoff.

### 3. DNS transport

UDP/53 is the default because most DNS exchanges are one small request, one small reply. A TCP handshake on every lookup would be wasteful.

DNS falls back to TCP/53 when:

- the response is too large for UDP (truncated, retry on TCP)
- DNSSEC responses run long
- zone transfers (`AXFR` / `IXFR`)

DoT is on its own port (853), so an operator can block it by blocking that one port. DoH is on port 443 mixed with normal HTTPS, so blocking DoH means blocking HTTPS, which breaks the rest of the web.

A school network often dislikes DoH because it bypasses local DNS-based filtering: captive portals, content blocklists, and parental controls all rely on seeing or redirecting DNS. DoH hides queries inside HTTPS to a third-party resolver, so local policy stops working.

### 4. HTTP/1.1 vs HTTP/2 vs HTTP/3 page load

#### HTTP/1.1

After the HTML (200 ms), 30 sub-resources go across 6 parallel connections. With no pipelining each connection serves its requests one at a time. Best case puts the slow one on its own connection:

- 1 connection: 1 slow + 4 fast = 2000 + 4*50 = 2200 ms
- 5 connections: 5 fast each = 250 ms

The page finishes when the slowest connection finishes:

```
total = 200 + 2200 = 2400 ms
```

#### HTTP/2

After the HTML (200 ms), all 30 streams run in parallel on one connection. The page finishes when the slowest stream does:

```
total = 200 + 2000 = 2200 ms
```

#### One lost segment in the slow transfer

In HTTP/2 the underlying TCP byte stream must be delivered in order. A loss on the slow stream stalls all bytes that arrived after it, even bytes belonging to the 29 fast streams. Those streams sit and wait until the retransmission arrives, adding about 80 ms.

In HTTP/3 each stream is reliable on its own. A loss on the slow stream only delays the slow stream. The 29 fast ones keep delivering and finish at 50 ms.

#### App-level vs TCP-level HOL

App-level HOL is what HTTP/1.1 pipelining had: responses came back in request order, so a slow response held up everything queued behind it. HTTP/2 fixes this by interleaving frames from many streams.

TCP-level HOL is at the transport. TCP delivers an in-order byte stream, so one lost segment blocks every byte after it, no matter which HTTP/2 stream they belong to. HTTP/2 cannot fix this because it sits on top of TCP. QUIC fixes it by moving stream framing below the reliability layer.

#### Pseudo-headers

- `:method` -> the method in the request line, e.g. `GET`
- `:path` -> the path in the request line, e.g. `/index.html`
- `:authority` -> the `Host` header

So `GET /index.html HTTP/1.1` with `Host: example.com` becomes `:method=GET`, `:path=/index.html`, `:authority=example.com` in the binary frame.

### 5. QUIC handshake and design

#### Time to first byte

With RTT = 80 ms:

- TCP + TLS 1.3: 2 * 80 = 160 ms
- QUIC 1-RTT: 1 * 80 = 80 ms
- QUIC 0-RTT: 0.5 * 80 = 40 ms

QUIC 0-RTT saves 160 - 40 = 120 ms.

#### Why UDP

The internet treats TCP and UDP as the only transports it understands. NATs, firewalls, and load balancers inspect TCP flags, and they drop or mishandle anything that is not TCP or UDP. UDP is dumb enough that they mostly leave it alone, so a new transport built on UDP can actually be deployed end-to-end today. A real new L4 protocol would have to wait for every middlebox to be updated, which never finishes.

#### User-space transport

In TCP, the kernel handles connection setup, retransmission, congestion control, and reordering. Changing TCP means a kernel update on every machine, which takes years. QUIC does all of this in a library inside the application. A browser release can ship a new congestion controller or a new handshake to a billion users in a normal update cycle. The kernel just sees UDP packets.

#### Connection migration

A phone is downloading a video on home Wi-Fi, then walks out and switches to LTE. The IP changes. TCP identifies a connection by `(src IP, src port, dst IP, dst port)`, so the connection breaks and the download restarts. QUIC identifies a connection by a connection ID inside the QUIC header, so the same connection survives the IP change and the download keeps going.
