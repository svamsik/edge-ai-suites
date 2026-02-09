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

<!--hide_directive
:::{toctree}
:hidden:

Usecase
how-to-configure-moxa-switch‎
how-to-configure-ptp
how-to-configure-vlan-on-moxa-switch
how-to-configure-vlan-on-all-machines
how-to-enable-tsn-traffic-shaping
how-it-run-mqtt-aggregator-and-visualization
how-to-run-rtsp-camera-and-ai-inference
how-to-run-sensor-data-producer‎
how-to-run-traffic-injector‎
‎
Source Code < https://github.com/open-edge-platform/edge-ai-suites/blob/main/metro-ai-suite/deterministic threat detection/docs/user-guide>
:::
hide_directive-->
