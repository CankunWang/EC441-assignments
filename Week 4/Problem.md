# EC441 Artifact – Multiple Access Protocols (Problem)

## Topic
Data Link Layer – Multiple Access Protocols

## Type
Problem + Worked Solution

---

# Problem: Efficiency of Multiple Access Protocols

Multiple nodes share a broadcast channel. When two nodes transmit at the same time, their frames collide and are lost. To solve this problem, networks use Multiple Access (MAC) protocols that determine how nodes share the channel.

---

# Question 1

Explain the **multiple access problem**. Why does it occur in broadcast networks?

## Solution

The **multiple access problem** occurs when several nodes share the same communication medium and attempt to transmit data simultaneously.

Examples include:

- Ethernet on a shared cable
- WiFi radio channels
- Satellite communication links

Because all nodes use the same medium, if two nodes transmit at the same time their signals interfere with each other. This produces a **collision**, which causes both frames to become corrupted and lost.

Therefore, a **MAC protocol** is needed to coordinate which node is allowed to transmit at a given time.

---

# Question 2

Pure ALOHA has throughput:

S = G e^(-2G)

where

- G = offered load (transmission attempts per frame time)

Find:

1. The value of G that maximizes throughput  
2. The maximum throughput Smax

## Solution

Throughput equation:

S = G e^(-2G)

Take derivative:

dS/dG = e^(-2G)(1 − 2G)

Set derivative to zero:

1 − 2G = 0

G = 1/2

Substitute back into throughput equation:

Smax = (1/2)e^(-1)

Smax ≈ 0.184

Therefore:

- Optimal load: **G = 0.5**
- Maximum efficiency: **about 18%**

This low efficiency occurs because collisions can happen within a **collision window of 2T**.

---

# Question 3

Slotted ALOHA improves performance.

The throughput equation is:

S = G e^(-G)

Find the maximum throughput.

## Solution

Take derivative:

dS/dG = e^(-G)(1 − G)

Set derivative equal to zero:

1 − G = 0

G = 1

Substitute back:

Smax = e^(-1)

Smax ≈ 0.368

Therefore:

- Maximum throughput ≈ **37%**

Slotted ALOHA is **twice as efficient as pure ALOHA** because it reduces the collision window from **2T to T**.

---

# Question 4

Explain the difference between the following MAC protocol families:

1. Channel partitioning  
2. Taking turns  
3. Random access  

## Solution

### 1. Channel Partitioning

The channel is divided into fixed pieces.

Examples:

- TDMA (Time Division Multiple Access)
- FDMA (Frequency Division Multiple Access)

Advantages:

- No collisions
- Predictable bandwidth

Disadvantages:

- Inefficient when few nodes are transmitting because unused slots are wasted.

---

### 2. Taking Turns

Nodes explicitly take turns transmitting.

Examples:

- Polling
- Token passing

Advantages:

- No collisions
- Fair scheduling

Disadvantages:

- Control overhead
- Possible single point of failure.

---

### 3. Random Access

Nodes transmit whenever they have data and recover from collisions.

Examples:

- ALOHA
- CSMA
- CSMA/CD

Advantages:

- Works well with bursty traffic
- Fully decentralized

Disadvantages:

- Collisions can still occur.

---

# Question 5

Why does classic Ethernet require a **minimum frame size of 64 bytes**?

## Solution

In CSMA/CD networks, a node must still be transmitting when the collision signal returns from the far end of the network.

Condition:

T ≥ 2τ

Where

- T = frame transmission time
- τ = propagation delay

Since

T = L / R

we obtain:

L ≥ 2τR

For classic Ethernet:

- Data rate R = 10 Mbps
- Round-trip propagation delay ≈ 50 µs

This gives a minimum frame size of about **500 bits**, which is **64 bytes**.

This ensures the sender detects collisions before finishing transmission.

---

# Key Takeaways

- Pure ALOHA maximum efficiency ≈ **18%**
- Slotted ALOHA maximum efficiency ≈ **37%**
- CSMA improves efficiency by sensing the channel before transmitting
- CSMA/CD detects collisions and aborts transmission early
- Ethernet minimum frame size is **64 bytes**

---

# Reflection

Multiple access protocols illustrate how distributed systems coordinate shared communication resources. Early protocols such as ALOHA prioritized simplicity but suffered from low efficiency. Later protocols such as CSMA/CD improved performance by sensing the channel and detecting collisions. Modern switched Ethernet networks eliminate collisions entirely by using full-duplex links.