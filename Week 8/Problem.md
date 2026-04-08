# Week 8 - TCP Part 1 Problem

## Problem

Assume:

- Client ISN = 12000
- Server ISN = 5000
- After setup, the client sends 900 bytes and then 600 bytes
- TCP uses cumulative ACKs

### 1. 3-way handshake

Write the three handshake segments. For each one, give:

1. flags
2. sequence number
3. acknowledgment number if valid

Also explain why `SYN` consumes one sequence number.

### 2. Byte-stream sequencing

After the handshake:

1. What sequence number is used for the first data segment?
2. What sequence number is used for the second data segment?
3. If both arrive in order, what ACK does the server send?
4. If the second segment is lost, what ACK does the server send?
5. Why does TCP count bytes instead of segments?

### 3. RTT estimation and RTO

Use:

- `SRTT_new = (1 - alpha) * SRTT_old + alpha * R`
- `RTTVAR_new = (1 - beta) * RTTVAR_old + beta * |SRTT_old - R|`
- `RTO = SRTT_new + 4 * RTTVAR_new`

Given:

- `alpha = 1/8`
- `beta = 1/4`
- `SRTT_old = 100 ms`
- `RTTVAR_old = 20 ms`
- `R = 140 ms`

Find:

1. `SRTT_new`
2. `RTTVAR_new`
3. `RTO`

Briefly state why TCP tracks both `SRTT` and `RTTVAR`.

### 4. Fast retransmit

The client sends these byte ranges:

- 12001-12900
- 12901-13500
- 13501-14100
- 14101-14700

Assume the second segment is lost and the next two arrive.

1. What ACK is sent after the third segment arrives?
2. What ACK is sent after the fourth segment arrives?
3. What triggers fast retransmit?
4. Why not retransmit after the first duplicate ACK?

### 5. Flow control

The receiver buffer is 16384 bytes.

- 4380 bytes are buffered
- The application reads 2000 bytes
- Then 6000 more bytes arrive

Find:

1. the initial free space
2. the advertised `rwnd` after the read
3. the remaining free space after the 6000 bytes arrive
4. what the sender does when `rwnd = 0`
5. the difference between flow control and congestion control

## Solution

### 1. 3-way handshake

Segment 1:

- flags: `SYN`
- seq: `12000`
- ack: not valid

Segment 2:

- flags: `SYN, ACK`
- seq: `5000`
- ack: `12001`

Segment 3:

- flags: `ACK`
- seq: `12001`
- ack: `5001`

`SYN` uses one sequence number so it can be acknowledged and retransmitted if it is lost.

### 2. Byte-stream sequencing

1. First data segment:
   `seq = 12001`, bytes `12001-12900`

2. Second data segment:
   `seq = 12901`, bytes `12901-13500`

3. If both arrive in order:
   `ACK = 13501`

4. If the second segment is lost:
   `ACK = 12901`

5. TCP counts bytes because TCP is a byte-stream protocol. The application does not see segment boundaries.

### 3. RTT estimation and RTO

`SRTT_new = (7/8) * 100 + (1/8) * 140 = 105 ms`

`RTTVAR_new = (3/4) * 20 + (1/4) * |100 - 140| = 15 + 10 = 25 ms`

`RTO = 105 + 4 * 25 = 205 ms`

`SRTT` is the average RTT. `RTTVAR` shows how much the RTT varies. TCP needs both so the timeout is not too small when delay changes a lot.

### 4. Fast retransmit

1. After the third segment arrives out of order:
   `ACK = 12901`

2. After the fourth segment arrives out of order:
   `ACK = 12901`

3. Fast retransmit starts after three duplicate ACKs for the same missing byte.

4. One duplicate ACK may just be packet reordering. Three duplicate ACKs are a better sign that a segment was lost.

### 5. Flow control

1. Initial free space:
   `16384 - 4380 = 12004 bytes`

2. After the application reads 2000 bytes:
   buffered data = `2380`
   `rwnd = 16384 - 2380 = 14004`

3. After 6000 more bytes arrive:
   buffered data = `2380 + 6000 = 8380`
   free space = `16384 - 8380 = 8004 bytes`

4. If `rwnd = 0`, the sender stops normal transmission and sends zero-window probes until the receiver advertises space again.

5. Flow control prevents receiver buffer overflow. Congestion control prevents too much traffic in the network. The sender is limited by `min(rwnd, cwnd)`.
