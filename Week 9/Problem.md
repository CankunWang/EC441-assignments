# Week 9 - TCP Congestion Control

This week I focused on the congestion-control side of TCP from Lecture 20, since Week 8 already covered handshake, byte numbering, ACKs, and basic flow control.

## Problem

Assume TCP Reno unless I say otherwise. I will use these variables:

- `cwnd`: congestion window
- `ssthresh`: slow-start threshold
- `MSS`: maximum segment size

### 1. Tracking `cwnd` and `ssthresh`

A sender starts with:

- `cwnd = 1 MSS`
- `ssthresh = 8 MSS`

Use these rules:

- in slow start, `cwnd` doubles every RTT
- in congestion avoidance, `cwnd` increases by `1 MSS` per RTT
- 3 duplicate ACKs mean mild congestion
- a timeout means severe congestion

Questions:

1. What are `cwnd` and `ssthresh` after the first three RTTs?
2. What happens once `cwnd` reaches `8 MSS`?
3. After two more RTTs, what is `cwnd`?
4. If 3 duplicate ACKs arrive when `cwnd = 10 MSS`, what are the new `cwnd` and `ssthresh`?
5. After one more RTT, what is `cwnd`?
6. If a timeout later happens when `cwnd = 8 MSS`, what are the new `cwnd` and `ssthresh`?

### 2. Throughput estimate

Use the lecture approximation

`Throughput ~= MSS / (RTT * sqrt(p))`

with:

- `MSS = 1460 bytes`
- `RTT = 80 ms`
- `p = 10^-5`

Questions:

1. What is the approximate throughput in bytes/s?
2. What is it in Mb/s?
3. If RTT doubles to `160 ms`, what happens to throughput?
4. Why do high RTT and even small loss rates hurt Reno so much?

### 3. BDP and window scaling

Suppose a path has:

- bandwidth = `1 Gb/s`
- RTT = `100 ms`

Questions:

1. What is the BDP in bits?
2. What is the BDP in bytes?
3. If the advertised window is limited to about `64 KB`, what throughput limit does that create?
4. What scale factor `2^n` is enough to cover the BDP?
5. What does this tell us about the relationship between TCP's window field and throughput?

### 4. Short explanation questions

1. How is congestion control different from flow control?
2. Why is ECN better than waiting for packet drops, if the network supports it?
3. Why does Reno usually favor shorter-RTT flows?
4. Why can HTTP/2 over TCP still have head-of-line blocking, while QUIC reduces that problem?

---

## Solution

### 1. Tracking `cwnd` and `ssthresh`

Start:

- `cwnd = 1 MSS`
- `ssthresh = 8 MSS`

After RTT 1, the sender is still in slow start, so `cwnd` doubles:

- `cwnd = 2 MSS`
- `ssthresh = 8 MSS`

After RTT 2:

- `cwnd = 4 MSS`
- `ssthresh = 8 MSS`

After RTT 3:

- `cwnd = 8 MSS`
- `ssthresh = 8 MSS`

Once `cwnd` reaches `ssthresh`, TCP leaves slow start and moves to congestion avoidance.

In congestion avoidance, growth is linear:

- after one more RTT: `cwnd = 9 MSS`
- after two more RTTs: `cwnd = 10 MSS`

If 3 duplicate ACKs arrive at `cwnd = 10 MSS`, Reno cuts the window in half:

- `ssthresh = 5 MSS`
- `cwnd = 5 MSS`

After one more RTT in congestion avoidance:

- `cwnd = 6 MSS`
- `ssthresh = 5 MSS`

If a timeout later happens when `cwnd = 8 MSS`, TCP reacts more aggressively:

- `ssthresh = 4 MSS`
- `cwnd = 1 MSS`

Summary:

| Event | `cwnd` | `ssthresh` |
|---|---:|---:|
| Start | 1 | 8 |
| After RTT 1 | 2 | 8 |
| After RTT 2 | 4 | 8 |
| After RTT 3 | 8 | 8 |
| After 1 RTT in CA | 9 | 8 |
| After 2 RTTs in CA | 10 | 8 |
| After 3 duplicate ACKs | 5 | 5 |
| After next RTT | 6 | 5 |
| After timeout at `cwnd = 8` | 1 | 4 |

The main point is that Reno treats 3 duplicate ACKs and timeout differently. Duplicate ACKs mean the path is still partly working, so the sender halves the window. A timeout is treated as a stronger sign of congestion, so the sender falls back to `1 MSS`.

### 2. Throughput estimate

Given:

- `MSS = 1460 bytes`
- `RTT = 80 ms = 0.08 s`
- `p = 10^-5`

First,

`sqrt(p) = sqrt(10^-5) ~= 0.003162`

So

`Throughput ~= 1460 / (0.08 * 0.003162)`

`Throughput ~= 1460 / 0.00025296`

`Throughput ~= 5.77 x 10^6 bytes/s`

So the approximate throughput is about `5.77 x 10^6 bytes/s`, or about `5.77 MB/s`.

To convert to bits per second:

`5.77 x 10^6 * 8 ~= 4.62 x 10^7 bits/s`

So the throughput is about `46.2 Mb/s`.

If RTT doubles to `160 ms`, throughput is cut in half because the formula is inversely proportional to RTT. That gives about `23.1 Mb/s`.

This is why Reno performs badly on long paths. The sender only grows the window gradually, and each control step takes roughly one RTT. Loss makes things worse because every loss event forces TCP to reduce `cwnd` and climb again.

### 3. BDP and window scaling

Given:

- bandwidth = `1 Gb/s = 10^9 bits/s`
- RTT = `100 ms = 0.1 s`

The bandwidth-delay product is

`BDP = bandwidth * RTT = 10^9 * 0.1 = 10^8 bits`

so the BDP is `100,000,000 bits`.

In bytes:

`100,000,000 / 8 = 12,500,000 bytes`

so the BDP is `12.5 MB`.

If the receive window is capped at `64 KB`, then the sender can only keep about `65,536` bytes in flight. That gives

`Throughput = Window / RTT = 65,536 / 0.1 = 655,360 bytes/s`

Converting to bits per second:

`655,360 * 8 = 5,242,880 bits/s`

so the practical limit is only about `5.24 Mb/s`.

To cover the full BDP, we need

`65,536 * 2^n >= 12,500,000`

and

`12,500,000 / 65,536 ~= 190.7`

Since `2^7 = 128` is too small but `2^8 = 256` is large enough, the smallest working value is `n = 8`.

This shows that a fast link by itself is not enough. If TCP cannot advertise a large enough window, then the sender cannot fill the path and throughput stays low.

### 4. Short explanation questions

Flow control protects the receiver. Congestion control protects the network. In TCP, flow control is tied to `rwnd`, while congestion control is tied to `cwnd`. The sender is really limited by `min(rwnd, cwnd)`.

ECN is better than pure loss-based signaling because it lets routers warn the sender before the queue overflows. The packet is marked instead of dropped, so the sender still learns that congestion is building but does not lose that packet's goodput.

Reno tends to favor short-RTT flows because they complete more control cycles per second. A short-RTT flow gets to increase its sending rate more often than a long-RTT flow sharing the same bottleneck.

HTTP/2 over TCP can still suffer head-of-line blocking because all streams share one ordered TCP byte stream. If one TCP segment is lost, later data cannot be delivered in order until retransmission arrives. QUIC reduces this by multiplexing streams independently over UDP and handling recovery per stream.
