# Week 01 – Physical Layer Problem: Capacity vs. Reliability (Shannon + BER)

## Problem Statement
For week 1's topic, I consider a baseband digital link modeled as an AWGN channel.

Given:
- Bandwidth: B = 10 MHz
- Received signal power: Prx = -90 dBm
- Noise spectral density: N0 = -174 dBm/Hz
- Target bit error rate (BER): Pb < 1e-6
- Signaling: bipolar NRZ (binary)

Tasks:
1) Try to compute the total noise power N over bandwidth B, then compute SNR in dB and linear.
2) Compute the Shannon capacity C (bits/s).
3) Using the BER constraint for bipolar NRZ in AWGN:
	   Pb = Q(sqrt(2 Eb/N0)),
   Then estimate the required Eb/N0 (in dB) to achieve Pb < 1e-6.
   Then use the relationship, which is Eb/N0 = (S/N) * (B/Rb),
   to compute the maximum bit rate Rb that satisfies the BER constraint.
4) Final feasible rate: R = min(C, Rb). Briefly explain which constraint dominates.

---

## Solution

### 1. Noise power and SNR
	Noise power over bandwidth B:
	N(dBm) = -174 + 10 log10(B)

	Here, B = 10 MHz = 10^7 Hz:
	10 log10(10^7) = 70 dB

	So:
	N = -174 + 70 = -104 dBm

	SNR(dB) = Prx - N = (-90) - (-104) = 14 dB

	Convert to linear:
	SNR = 10^(14/10) = 10^1.4 ≈ 25.12

---

### 2. Shannon capacity
	C = B log2(1 + SNR)

	C = 10^7 * log2(1 + 25.12) = 10^7 * log2(26.12)

	Since 2^4.7 ≈ 25.99, log2(26.12) = 4.71

	So:
	C ≈ 10^7 * 4.71 = 4.71e7 bits/s =47.1 Mbps

---

### 3. BER constraint → required Eb/N0 and max Rb
	For bipolar NRZ in AWGN:
	Pb = Q(sqrt(2 Eb/N0))

	Target Pb < 1e-6.
	A standard approximation is Q(4.75) = 1e-6, so: sqrt(2 Eb/N0) > 4.75

	Square both sides:
	2 Eb/N0 > 4.75^2 = 22.5625
	Eb/N0 > 11.281 (linear)

	Convert to dB:
	Eb/N0(dB) = 10 log10(11.281) = 10.52 dB

	Now use:
	Eb/N0 = (S/N) * (B/Rb)
	=> Rb = (S/N) * B / (Eb/N0)

	Rb = 25.12 * 10^7 / 11.281
	   = (25.12/11.281) * 10^7
	   = 2.23e7 bits/s
	   = 22.3 Mbps

---

### 4. Feasible rate and conclusion
Feasible rate:
R = min(C, Rb) = min(47.1 Mbps, 22.3 Mbps) = 22.3 Mbps

Conclusion:
Here the BER (reliability) constraint is tighter than Shannon capacity.
Even though the channel could support ~47 Mbps in theory, achieving BER < 1e-6 requires lowering the bit rate to increase Eb/N0 per bit.
