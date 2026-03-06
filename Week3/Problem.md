# Ethernet Addressing, Switching, and ARP – Problem Set

## Topic

Ethernet: addressing, switching, ARP

## Type

Problem with worked solution

---

# Problem 1 – Ethernet Frame Structure


An Ethernet frame contains the following fields:

Preamble + SFD
Destination MAC
Source MAC
Type
Payload
FCS

Questions:
1. What is the minimum Ethernet frame size?
2. What is the maximum Ethernet frame size?
3. Why does Ethernet require a minimum frame size?
---

## Solution

### 1. Minimum frame size

Preamble + SFD      8
Destination MAC     6
Source MAC          6
Type                2
Payload            46
FCS                 4
-----------------------
Total              72 bytes


However, the official Ethernet frame size **does not include the preamble and SFD**.

Destination MAC     6
Source MAC          6
Type                2
Payload            46
FCS                 4
-----------------------
Total              64 bytes

Minimum Ethernet frame size = 64 bytes


---

### 2. Maximum frame size

Maximum payload = **1500 bytes**.

Destination MAC   6  
Source MAC        6  
Type              2  
Payload        1500  
FCS               4  
-------------------  
Total           1518 bytes

Maximum Ethernet frame size = **1518 bytes**.

This is why the standard IP MTU is **1500 bytes**.

---

### 3. Why Ethernet requires a minimum frame size

Early Ethernet used **CSMA/CD (Carrier Sense Multiple Access with Collision Detection)**.

To detect collisions, the sender must still be transmitting when the collision signal returns from the far end of the network.

If frames were too short:

sender finishes transmission  
before collision signal arrives

The sender would not detect the collision.

Therefore the minimum frame size ensures:

transmission time ≥ round-trip propagation delay

For 10 Mbps Ethernet:

Lmin = 2τR

which equals **512 bits (64 bytes)**.

---

# Problem 2 – MAC Address Structure

Given the MAC address:

A4:C3:F0:85:AC:2D

Answer the following:

1. How many bits are in a MAC address?
2. Which part identifies the manufacturer?
3. What is the broadcast MAC address?
---

## Solution

### 1. MAC address length

A MAC address is **48 bits (6 bytes)**.

Example representation:

A4:C3:F0:85:AC:2D

Each pair represents **1 byte in hexadecimal**.

---

### 2. Manufacturer identifier

The first **3 bytes (24 bits)** are called the **OUI (Organizationally Unique Identifier)**.

A4:C3:F0

This prefix is assigned by IEEE to hardware manufacturers.

The remaining **3 bytes** identify the specific device.

---

### 3. Broadcast MAC address

Broadcast MAC address:

FF:FF:FF:FF:FF:FF

Frames sent to this address are delivered to **all devices in the LAN**.

---

# Problem 3 – ARP Resolution

Host A:

IP: 192.168.1.10  
MAC: AA:AA:AA:AA:AA:AA

Host B:

IP: 192.168.1.20  
MAC: BB:BB:BB:BB:BB:BB

Host A wants to send data to Host B.

---

## Questions

1. What message does Host A send first?
    
2. Is the message broadcast or unicast?
    
3. What does Host B reply with?
    

---

## Solution

### Step 1 – ARP Request

Host A does not know the MAC address of **192.168.1.20**.

It sends an ARP request:

Ethernet Destination: FF:FF:FF:FF:FF:FF  
Message: Who has 192.168.1.20?

This message is **broadcast** to all hosts in the LAN.

---

### Step 2 – ARP Reply

Host B responds:

Ethernet Destination: AA:AA:AA:AA:AA:AA  
Message: 192.168.1.20 is at BB:BB:BB:BB:BB:BB

This reply is **unicast**.

---

### Step 3 – Data Transmission

Host A stores the mapping in its ARP cache:

192.168.1.20 → BB:BB:BB:BB:BB:BB

Then Host A sends the Ethernet frame:

Destination MAC: BB:BB:BB:BB:BB:BB  
Source MAC: AA:AA:AA:AA:AA:AA

---

# Problem 4 – Ethernet Switch Learning

A switch initially has an **empty forwarding table**.

Network:

Port 1 → Host A  
Port 2 → Host B  
Port 3 → Host C

Frame sequence:

1. A → B  
2. B → A  
3. C → A

---

## Solution

### Frame 1: A → B

Switch receives frame on **port 1**.

Action:

learn A → port 1  
destination B unknown → flood

Forwarding table:

A → 1

---

### Frame 2: B → A

Switch receives frame on **port 2**.

Action:

learn B → port 2  
A known → forward to port 1

Forwarding table:

A → 1  
B → 2

---

### Frame 3: C → A

Switch receives frame on **port 3**.

Action:

learn C → port 3  
A known → forward to port 1

Final table:

A → 1  
B → 2  
C → 3

This automatic process is called **switch self-learning**.

---

# Reflection

This problem set demonstrates several key Ethernet concepts:

- The **Ethernet frame format** defines how data is encapsulated at the link layer.
    
- **MAC addresses** identify devices on a local network.
    
- **ARP** resolves IP addresses to MAC addresses.
    
- **Switches automatically learn host locations** using MAC addresses.
    

Together, these mechanisms allow efficient communication within a LAN.

---
