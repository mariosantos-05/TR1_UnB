# Physical and Data Link Layer Simulator

This project is a simulator developed for the **Teleinformática e Redes I(UnB)** course, implementing core functionalities of the **Physical Layer** and **Data Link Layer** of the OSI model.

---

## 📘 Overview

The simulator aims to reproduce the transmission and reception processes that occur at the two lowest layers of a communication system.

It includes:

- **Baseband and carrier modulation** (Physical Layer)
- **Framing, error detection, and error correction protocols** (Data Link Layer)
- **Noise simulation** based on Gaussian random variables
- **Graphical interface (GTK)** for configuration and signal visualization

---

## 🧠 Implemented Concepts

### 🔹 Physical Layer

#### Digital Modulation

- Non-Return to Zero Polar (**NRZ-Polar**)
- **Manchester**
- **Bipolar**

#### Carrier Modulation

- **Amplitude Shift Keying (ASK)**
- **Frequency Shift Keying (FSK)**
- **Phase Shift Keying (QPSK)**
- **16-Quadrature Amplitude Modulation (16-QAM)**

---

### 🔹 Data Link Layer

#### Framing Protocols

- Character Count
- Flags with Byte/Character Insertion
- Flags with Bit Insertion

#### Error Detection

- Even Parity Bit
- **Checksum**
- **CRC-32 (IEEE 802)**

#### Error Correction

- **Hamming Code**

---

## ⚙️ Architecture

![Architecture Diagram](/dev_diagram.png)

Each layer is modularized and implemented in separate files:

- `CamadaFisica/` — Physical Layer functions
- `CamadaEnlace/` — Data Link Layer functions
- `InterfaceGUI/` — GTK-based interface for user input and signal output
- `Simulador/` — Main simulation control

---

## 💻 Requirements

- **Language:** Python 3 or C++
- **Operating System:** Linux
- **Dependencies:**
  - [GTK](https://www.gtk.org/docs/language-bindings/) (Python GTK3 or C++ GTK+)
  - Standard libraries only (no external CRC or encoding libraries)

---

## 🚀 Running the Simulator

```bash
to be done...


```
