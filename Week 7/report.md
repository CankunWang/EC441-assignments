# Week 7 Report: ICMP, NAT, Fragmentation, and IPv6 in Practice

## Introduction
For this week's assignment I wanted to check how much of Lecture 17 I could actually see in packet captures instead of just repeating the definitions. I focused on ICMP behavior, TTL expiration, one fragmentation case, local addressing, and a small IPv6 comparison.

I used the `WLAN` interface for the IPv4 tests. During the experiment it had address `192.168.99.161/24` with gateway `192.168.99.1`. The main external target was `8.8.8.8`. I saved two captures:

- `week7_wlan_icmp.pcapng` for the IPv4 tests on WLAN
- `week7_loopback_ipv6.pcapng` for a small IPv6 test on loopback

## What I Did
I used `ping`, `tracert`, `ipconfig /all`, `dumpcap`, and `tshark`.

The experiments were straightforward:

1. Run a normal `ping` to `8.8.8.8`.
2. Run `tracert -d -h 4 8.8.8.8` and inspect the ICMP replies.
3. Try a larger `ping` with DF set using `ping -n 2 -f -l 2000 8.8.8.8`.
4. Record the local IPv4 configuration with `ipconfig /all`.
5. Capture `ping -6 -n 2 ::1` so I would at least have one real IPv6 packet to compare with IPv4.

## Experiment 1: IPv4 `ping`
`ping -n 3 8.8.8.8` worked normally. The replies were:

- Reply 1: `time=11ms TTL=116`
- Reply 2: `time=10ms TTL=116`
- Reply 3: `time=10ms TTL=116`

In Wireshark, the pattern was exactly what I expected:

| Frame | Source | Destination | TTL | ICMP Type | Code | Meaning |
|---|---|---|---:|---:|---:|---|
| 2 | 192.168.99.161 | 8.8.8.8 | 128 | 8 | 0 | Echo Request |
| 3 | 8.8.8.8 | 192.168.99.161 | 116 | 0 | 0 | Echo Reply |
| 4 | 192.168.99.161 | 8.8.8.8 | 128 | 8 | 0 | Echo Request |
| 5 | 8.8.8.8 | 192.168.99.161 | 116 | 0 | 0 | Echo Reply |
| 7 | 192.168.99.161 | 8.8.8.8 | 128 | 8 | 0 | Echo Request |
| 8 | 8.8.8.8 | 192.168.99.161 | 116 | 0 | 0 | Echo Reply |

The main thing I wanted to confirm here was simple: `ping` is really using ICMP directly. There was no TCP or UDP session involved. The outgoing TTL of `128` also fits what I usually expect from Windows.

The return TTL of `116` is interesting because it shows the reply had already crossed multiple hops before reaching my machine. I cannot recover the full path from that number alone, but it is a good reminder that the reply is not coming from a directly connected host.

## Experiment 2: `tracert` and TTL Expiration
Then I ran `tracert -d -h 4 8.8.8.8`. The visible hops were:

| Hop | Address | Observed RTTs |
|---|---|---|
| 1 | 192.168.99.1 | 2 ms, 2 ms, 1 ms |
| 2 | 38.42.97.1 | 5 ms, 4 ms, 4 ms |
| 3 | 38.42.96.0 | 5 ms, 4 ms, 4 ms |
| 4 | 62.115.203.48 | *, 4 ms, 4 ms |

The capture matched that output well:

| Frame | Source | Destination | Outgoing TTL | Reply Source | Reply Type | Meaning |
|---|---|---|---:|---|---:|---|
| 9 | 192.168.99.161 | 8.8.8.8 | 1 | 192.168.99.1 | 11 | Time Exceeded |
| 15 | 192.168.99.161 | 8.8.8.8 | 2 | 38.42.97.1 | 11 | Time Exceeded |
| 21 | 192.168.99.161 | 8.8.8.8 | 3 | 38.42.96.0 | 11 | Time Exceeded |
| 30 | 192.168.99.161 | 8.8.8.8 | 4 | 62.115.203.48 | 11 | Time Exceeded |

This was probably the clearest part of the whole assignment. Instead of just saying "TTL decreases at each hop," I could actually see the result. Windows `tracert` on this machine sent ICMP Echo Requests with TTL values `1`, `2`, `3`, and `4`, and the routers that dropped them replied with ICMP Type `11`, Code `0`.

One detail I noticed is that this Windows version of `tracert` is using ICMP rather than UDP. Another detail is that I stopped at four hops, so the trace never reached `8.8.8.8` itself. What I captured here is the discovery process, not the final destination response.

## Experiment 3: Large Packet with DF Set
Next I tried `ping -n 2 -f -l 2000 8.8.8.8`.

Both attempts failed with:

- `Packet needs to be fragmented but DF set.`
- `Packet needs to be fragmented but DF set.`

So the loss rate was `100%`.

At first I expected to see an ICMP "Fragmentation Needed" message in the capture. What actually happened was a little different: on the WLAN capture I did not see an ICMP Type `3`, Code `4` packet coming back from the network.

My interpretation is that the failure was detected locally before the oversized packet was really sent out on the path I was capturing. I cannot prove the full internal behavior of the Windows stack from this alone, but that explanation fits the evidence better than assuming a remote router generated a message that never appeared in the capture.

So this experiment still shows the basic idea from lecture: large packets plus DF can fail. It just failed in a more local way than I originally expected.

## Experiment 4: NAT and Local Addressing
From `ipconfig /all`, the active `WLAN` interface had:

- IPv4 address: `192.168.99.161`
- Subnet mask: `255.255.255.0`
- Default gateway: `192.168.99.1`
- DHCP server: `192.168.99.1`
- DNS servers: `8.8.8.8` and `1.1.1.1`

The important point here is that `192.168.99.161` is a private address. That means this machine is not using a publicly routable IPv4 address directly.

Since the host could still reach `8.8.8.8`, some device on the path had to translate the private source address before the traffic left the local network. The most likely place is the gateway or something beyond it. This is still an inference, not a direct measurement of the NAT table, so I do not want to overclaim it. But based on the addressing and the successful public connectivity, NAT is the most reasonable explanation.

## Experiment 5: IPv6 Packet Observation
I wanted to compare IPv4 with IPv6 on the same active interface, but `ipconfig /all` did not show a usable IPv6 configuration on `WLAN` during the experiment. Because of that, I switched to a smaller but still real capture: `ping -6 -n 2 ::1` on loopback.

The capture showed:

| Frame | Source | Destination | Hop Limit | Next Header | ICMPv6 Type | Meaning |
|---|---|---|---:|---:|---:|---|
| 1 | ::1 | ::1 | 128 | 58 | 128 | Echo Request |
| 2 | ::1 | ::1 | 128 | 58 | 129 | Echo Reply |
| 3 | ::1 | ::1 | 128 | 58 | 128 | Echo Request |
| 4 | ::1 | ::1 | 128 | 58 | 129 | Echo Reply |

Even though this was only loopback traffic, it still gave me one useful packet-level comparison. IPv6 uses `Hop Limit` where IPv4 uses `TTL`, and it uses `Next Header` where IPv4 uses `Protocol`. In this capture, `Next Header = 58`, which identifies ICMPv6.

This is obviously not as strong as an end-to-end IPv6 path capture, but it was still better than writing about the IPv6 header only from lecture notes.

## Discussion
The strongest parts of this assignment were the `ping` and `tracert` captures because they lined up very clearly with the lecture material. `ping` showed the Echo Request and Echo Reply pattern directly. `tracert` made TTL expiration visible in a way that is much easier to remember than the textbook explanation by itself.

The large-packet test was the least clean result, but I think it was still useful. It reminded me that the network behavior discussed in class does not always show up in the most idealized form in a real system. Sometimes the host OS handles part of the problem before the packet ever reaches the wider network.

The NAT section is also a good example of the difference between direct observation and inference. I did not capture the translation itself, so I should not write as if I saw it happen. What I can say confidently is that the machine had a private IPv4 address and still reached a public destination, which makes NAT the sensible explanation.

## Limitations
There were a few clear limits in this experiment:

- I mostly captured ICMP, so I was not looking at all traffic types.
- The IPv6 part used loopback instead of a real external IPv6 route.
- The NAT conclusion was inferred from configuration and connectivity, not directly captured at the gateway.

## Conclusion
Overall, this lab made Lecture 17 feel much less abstract. I could see ICMP Echo Request and Echo Reply in the `ping` capture, and I could see ICMP Time Exceeded replies in the `tracert` capture when TTL expired at each hop. The fragmentation test also produced a real failure case, even though the failure seemed to be local rather than a router response captured on the wire.

The IPv6 part was limited, but it still gave me one real example of how IPv6 headers differ from IPv4. The NAT part was partly interpretive, but the private address on `WLAN` and successful access to `8.8.8.8` make that interpretation reasonable. In short, the report is not just repeating the lecture content: the packet captures show where the lecture matched what this machine actually did, and where the real system behavior was a little messier.
