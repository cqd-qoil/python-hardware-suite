# Quantum Optics Hardware Control Suite
---

This Python project provides a suite of tools for controlling and monitoring hardware used in experiments at QOIL. The suite includes scripts for **monitoring equipment**, **controlling motorised stages**, **data acquisition**, and more, making it a good starting point for managing your experiment.

The project is structured to allow flexibility and modularity, so users can easily extend or modify individual components based on their specific experimental setup.

---

## Features

### 1. **Monitoring Equipment**
- Ocean Optics USB spectrometers

### 2. **Motorised Stage Control**
- Newport SMC100CC servo motors ("white boxes")

### 3. **Data Acquisition**
- UQDevices Logic16 counting card
- Thorlabs PM100 Power Meter
- MCC DAQ devices ("blue boxes")

---

## Installation

To set up the environment and install the project dependencies, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/cqd-qoil/python-hardware-suite.git
   cd python-hardware-suite
   ```

2. **Set up a virtual environment (optional but recommended)**:

    ```python
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3. **Install dependencies and update submodules**:
    ```python
    pip install -r requirements.txt
    ```
    ```python
    git submodule update --init --recursive
    ```
4. **Install the project**:
    ```python
    python install.py
    ```
