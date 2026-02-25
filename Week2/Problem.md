
## Design and Analysis of a Block Code under Error Control Constraints

---

## Problem Statement

Design a link-layer block code for a communication system.

Requirements:

1. The code must **guarantee detection of up to 2 bit errors**.
2. The code must **guarantee correction of up to 1 bit error**.
3. The code should **maximize the code rate**.
4. Use the smallest possible codeword length nnn that satisfies the requirements.

Questions:

---

### (a)

Using the **dmin theorem**, determine the minimum required dmin

---

### (b)

Find the smallest n and corresponding k that satisfy the requirement.

---

### (c)

Construct a valid code (list all codewords).

---

### (d)

Compute:
- Code rate Rc
- All pairwise Hamming distances
- Verify dmin

---

### (e)

List all valid (ec,ed) pairs allowed by the dmin theorem.

---

### (f)

Explain the tradeoff between detection and correction in this design.  
Would ARQ or pure FEC be more bandwidth-efficient in a typical networking scenario?

---


##  Solution


### (a) Required Minimum Distance

We use the quick reference rules:

To detect ddd errors:
```
dmin≥d+1
```

To correct ddd errors:
```
dmin≥2d+1
```

We need:

- Detect 2 errors → dmin≥3
- Correct 1 error → dmin≥3

Therefore:

Minimum possible value will be 3

---

### (b) Smallest Possible Code Length

We want:

- dmin=3
- Smallest possible n
- Maximize k

---

### Try n=3

Maximum distance between two 3-bit words is 3.

If we only choose:

{000,111}

Then:

- k=1
- Rc=1/3

This satisfies dmin=3

If we try more than 2 codewords:

Minimum distance drops to 2.

Therefore:

n=3,k=1

---

### (c) Code Construction

Choose maximally separated codewords:

C={000,111}

Mapping:

|Data|Codeword|
|---|---|
|0|000|
|1|111|

---

### (d) Code Analysis

### Code Rate

Rc=k/n=1/3

---

#### Hamming Distance

dist(000,111)=3

Thus:

dmin=3

Verified.

---

### (e) Valid (ec,ed)(e_c, e_d)(ec​,ed​) Pairs

Using the theorem:

ec+ed≤dmin−1=2

Possible pairs:

|ece_cec​|ede_ded​|
|---|---|
|0|2|
|1|1|

---

#### Interpretation

1. (0, 2) → Pure detection (best detection)
2. (1, 1) → Pure correction (best correction)

---

### (f) Tradeoff Discussion

#### Detection vs Correction

Each unit of correction reduces detection capability.

For dmin=3

- Maximum detection: 2 errors
- Maximum correction: 1 error

You cannot have both.

---

#### Networking Perspective

In practical networking:

- Links are bidirectional.
- BER is usually low.
- Retransmission is cheap.

Thus:

ARQ (detection only) is more bandwidth-efficient.

Reason:

Correction requires more redundancy per bit transmitted.

For example:

- This code has rate 1/3.
    
- A simple parity code has rate close to 1.
    

Hence:

Detection + retransmission is typically 3–5× more efficient than FEC.