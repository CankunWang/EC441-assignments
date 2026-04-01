# Week 7 Report: ICMP, NAT, Fragmentation, and IPv6 in Practice

## Introduction
This report examines how the main ideas from Lecture 17 appear in real network traffic on a host that uses private IPv4 addressing and also supports IPv6. The discussion focuses on ICMP behavior, TTL-based path discovery, fragmentation-related behavior, and the difference between IPv4 connectivity through NAT and IPv6 connectivity with larger address space and a simpler base header.

## Background
ICMP supports error reporting and network diagnostics at the network layer. Tools such as `ping` and `tracert` depend on ICMP messages rather than TCP or UDP payload exchange. IPv4 also includes fragmentation support in the base header, but modern networks try to avoid fragmentation because it adds overhead and creates reliability and security concerns. NAT extends the useful life of IPv4 by allowing many private hosts to share one public address, while IPv6 is designed to restore large-scale addressability with a simpler header format.

## Method
The analysis is based on small experiments using:
- Wireshark
- `ping`
- `tracert`
- `ipconfig`

The workflow is:
1. Capture an IPv4 `ping` exchange and identify ICMP request and reply packets.
2. Run `tracert` to a public destination and interpret the returned ICMP messages hop by hop.
3. Test a large ping payload and analyze whether fragmentation occurs or whether MTU-related limits appear.
4. Record local interface information and classify the observed IPv4 and IPv6 addresses.
5. Compare one IPv4 packet and one IPv6 packet to highlight major header differences.

## Analysis Focus
The report is organized around four connected questions:
1. How does ICMP appear during `ping`?
2. How does `tracert` rely on TTL expiration and ICMP Time Exceeded messages?
3. What happens when packet size approaches or exceeds path MTU limits?
4. How do private IPv4 plus NAT and IPv6 addressing differ in practical observation?

## Discussion
The packet captures and command output are used to connect protocol definitions from class to actual traffic. The discussion centers on whether observed behavior matches the lecture model and where practical details add complexity, especially in the cases of NAT and fragmentation avoidance.

## Conclusion
The report argues that `ping` operates through ICMP, `tracert` depends on TTL expiration and ICMP responses, private IPv4 connectivity typically relies on NAT, IPv6 simplifies the base header compared with IPv4, and fragmentation is generally avoided when Path MTU Discovery works correctly.
