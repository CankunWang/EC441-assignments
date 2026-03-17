# EC441 Problem — Network Layer (Forwarding and Longest Prefix Match)

## Problem

Consider the following forwarding table in a router:

| Prefix            | Next Hop      | Interface |
|-------------------|--------------|-----------|
| 0.0.0.0/0         | 203.0.113.1  | eth0      |
| 10.0.0.0/8        | 10.255.0.1   | eth1      |
| 10.1.0.0/16       | 10.1.255.1   | eth2      |
| 10.1.2.0/24       | 10.1.2.254   | eth3      |
| 192.168.32.0/20   | 192.168.32.1 | eth4      |

---

### (a)

For each destination IP address below, determine:

- The matching prefix  
- The outgoing interface  

1. 10.1.2.5  
2. 10.5.6.7  
3. 192.168.33.5  
4. 192.168.48.1  

---

### (b)

Explain why longest prefix match (LPM) is required in IP forwarding.

---

### (c)

Describe the step-by-step forwarding process inside a router when a packet arrives.

---

## Solution

---

### (a)  Results

A router may find multiple matching prefixes for a destination IP. The rule is to select the most specific match, eg., the prefix with the greatest length.

---

#### 1. Destination: 10.1.2.5

Matches:
- 0.0.0.0/0  
- 10.0.0.0/8  
- 10.1.0.0/16  
- 10.1.2.0/24  

Longest prefix: /24  

**Result: eth3**

---

#### 2. Destination: 10.5.6.7

Matches:
- 0.0.0.0/0  
- 10.0.0.0/8  

Longest prefix: /8  

**Result: eth1**

---

#### 3. Destination: 192.168.33.5

192.168.32.0/20 range:
- 192.168.32.0 → 192.168.47.255  

192.168.33.5 is within this range  

**Result: eth4**

---

#### 4. Destination: 192.168.48.1

Outside the /20 range  

Matches:
- 0.0.0.0/0  

**Result: eth0 (default route)**

---

### Final Answers

| Destination IP   | Matching Prefix      | Interface |
|------------------|---------------------|-----------|
| 10.1.2.5         | 10.1.2.0/24         | eth3      |
| 10.5.6.7         | 10.0.0.0/8          | eth1      |
| 192.168.33.5     | 192.168.32.0/20     | eth4      |
| 192.168.48.1     | 0.0.0.0/0           | eth0      |

---

### (b) Why Longest Prefix Match is Necessary

- A destination IP may match multiple prefixes  
- Longer prefixes are more specific  
- Routers must choose the most specific route  
- CIDR relies on overlapping prefixes  

Without LPM:
- Routing becomes ambiguous  
- Packets may take incorrect paths  

---

### (c) Router Forwarding Process

#### Step 1: Receive packet
- Packet arrives at input interface  
- Bits are reconstructed into a packet  

#### Step 2: Check IP header
- Verify checksum  
- Decrement TTL  

#### Step 3: TTL handling
- If TTL = 0 → drop packet  
- Send ICMP Time Exceeded  

#### Step 4: Forwarding table lookup
- Extract destination IP  
- Perform longest prefix match  
- Determine output interface  

#### Step 5: Forward packet
- Send to output interface  
- Use ARP if needed to resolve MAC  

---

## Summary

This problem covers:

- Longest prefix match  
- Forwarding table lookup  
- Router data plane operations  

It reflects core network layer concepts of forwarding and routing.