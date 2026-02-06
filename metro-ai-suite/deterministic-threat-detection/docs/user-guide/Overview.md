## Overview

This document describes a **Time-Sensitive Networking (TSN)** sample application designed to demonstrate deterministic, low-latency delivery of **AI-processed video and sensor data** in the presence of best-effort background traffic.

The sample showcases:
- Multi-camera video acquisition over Ethernet
- Precise time synchronization using **IEEE 802.1AS (gPTP)**
- End-to-end latency measurement using PTP timestamps
- AI inference on synchronized video frames
- MQTT-based data aggregation and visualization
- Traffic interference using `iperf`
- Traffic protection using **IEEE 802.1Qbv (Time-Aware Shaper)**

---

Refer to [Usecase.md](./Usecase.md) for detailed steps to set up and run the sample, which demonstrates the use of TSN in this use case.