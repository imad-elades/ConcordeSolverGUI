# Concorde Vision Solver

## Overview

Concorde Vision Solver is a high-precision Graphical User Interface (GUI) for the Concorde TSP Solver. It provides a seamless bridge between modern data formats (Excel/CSV) and the mathematical power of Concorde, ensuring the calculation of the optimal tour for Traveling Salesman Problems.

This application is designed for Windows environments, leveraging the Windows Subsystem for Linux (WSL2) to execute the Concorde binary while offering a native Python user interface for data management and visualization.

**Key Features:**
*   **Optimal Solutions:** Guarantees the exact optimal solution using the Concorde solver.
*   **High Precision:** Implements a rigorous Euclidean projection referenced to Gibraltar (Latitude 36.57 degrees), ensuring consistent meter-level accuracy for GPS coordinates.
*   **Data Integration:** Native support for Excel (.xlsx) and CSV files with automatic column detection.
*   **Interactive Visualization:** Generates interactive HTML maps showing the optimal tour path.
*   **Configurable:** Allows fine-tuning of Concorde parameters (Seed, Time Limit, Fast Cuts).

## Prerequisites

*   **Operating System:** Windows 10 or Windows 11.
*   **Architecture:** x64 system.
*   **Administrator Access:** Required for enabling WSL features.

## Installation Guide

This guide assumes a fresh Windows installation. Follow these steps sequentially to set up the environment.

### Phase 1: Setup Windows Subsystem for Linux (WSL2)

The Concorde solver requires a Linux environment to run reliably. We use WSL2 to achieve this without a dual-boot setup.

1.  Open PowerShell as Administrator.
2.  Run the following command to enable WSL features:
    ```powershell
    wsl --install
    ```
3.  **Restart your computer** when prompted.
4.  After restart, Ubuntu should install automatically. If not, open the Microsoft Store and install "Ubuntu 22.04 LTS".
5.  Open Ubuntu from the Start menu. It will complete the setup and ask for a username and password. Choose any username/password you prefer.

### Phase 2: Compiling Concorde

We need to compile the Concorde solver specifically for your system.

1.  Open your Ubuntu terminal (WSL).
2.  Update the system and install build tools:
    ```bash
    sudo apt update
    sudo apt install build-essential gcc make curl
    ```
3.  Create the directory structure (strictly required for this application):
    The application expects Concorde to be located at `/mnt/d/Concorde`.
    
    *Note: If you do not have a D: drive, you will need to modify the `paths` dictionary in `Concorde_Vision_Solver.py`.*

    ```bash
    # Create directory on D: drive (ensure D: exists in Windows)
    mkdir -p /mnt/d/Concorde/bin
    
    # Download QSopt (Linear Programming solver required by Concorde)
    cd /mnt/d/Concorde
    mkdir qsopt
    cd qsopt
    curl -O http://www.math.uwaterloo.ca/~bico/qsopt/codes/QSopt_generator.tar.gz
    tar -xzvf QSopt_generator.tar.gz
    
    # Download Concorde Source
    cd /mnt/d/Concorde
    curl -O http://www.math.uwaterloo.ca/tsp/concorde/downloads/codes/src/co031219.tgz
    tar -xzvf co031219.tgz
    ```
4.  Compile Concorde with QSopt:
    ```bash
    cd /mnt/d/Concorde/concorde
    ./configure --with-qsopt=/mnt/d/Concorde/qsopt
    make
    
    # Copy the executable to the bin folder
    cp TSP/concorde /mnt/d/Concorde/bin/
    ```
5.  Verify the installation:
    ```bash
    /mnt/d/Concorde/bin/concorde -h
    ```
    This should display the help usage for Concorde.

### Phase 3: Python Environment Setup

1.  Download and Install Python 3.8 or newer from [python.org](https://www.python.org/).
    *   **Crucial:** Check the box "Add Python to PATH" during installation.
2.  Open Command Prompt or PowerShell (Windows).
3.  Navigate to the project directory:
    ```powershell
    cd D:\Concorde\Concorde_Graphique
    ```
4.  Install the required Python dependencies:
    ```powershell
    pip install -r requirements.txt
    ```

## Usage

1.  Navigate to the application folder:
    ```powershell
    cd D:\Concorde\Concorde_Graphique
    ```
2.  Launch the application:
    ```powershell
    python Concorde_Vision_Solver.py
    ```
3.  **In the Application:**
    *   Click **Select File** to load your Excel or CSV data.
    *   Ensure the columns for ID, Latitude, and Longitude are correctly approximated.
    *   Adjust Concorde parameters if necessary (e.g., set a Timeout for very large datasets).
    *   Click **Run Optimization**.
    *   Once complete, use the buttons to inspect the results in Excel or view the interactive map.

## Technical Details

**Coordinate Projection:**
To ensure maximum precision suitable for Concorde's Euclidean distance calculations (`EUC_2D`), this tool uses a custom Equirectangular projection.
*   **Reference Latitude:** 36.57 degrees (Gibraltar).
*   **Precision:** Coordinates are converted to meters with 6 decimal places.
*   This specific projection minimizes distortion for the target geographic area and ensures metric consistency between the optimization engine and the reported results.

## Credits

**Developer:** iM@Des
**Copyright:** (c) 2026 iM@Des. All Rights Reserved.

**Core Solver:**
This software acts as a graphical frontend for the **Concorde TSP Solver**, developed by William Cook, David Applegate, Robert Bixby, and Vasek Chvatal.
Reference: [http://www.math.uwaterloo.ca/tsp/concorde/](http://www.math.uwaterloo.ca/tsp/concorde/)

## License

This project is proprietary. Unauthorized copying, modification, or distribution is strictly prohibited.
The underlying Concorde solver is subject to its own academic use license.
