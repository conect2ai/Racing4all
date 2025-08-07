# Racing4All - Data Acquisition for Sim Racing

Welcome to **Racing4All**! This repository is dedicated to providing tools and scripts for acquiring telemetry and session data from the popular racing simulators **iRacing** and **Assetto Corsa Competizione (ACC)**.

The goal is to centralize programming solutions so that virtual drivers, data engineers, and enthusiasts can extract valuable information from their track sessions—whether for performance analysis, setup development, or just out of curiosity.

## 🏁 Supported Simulators

Currently, the project provides scripts for the following simulators:

* **iRacing**
* **Assetto Corsa Competizione (ACC)**

## ✨ Key Features

My scripts allow for the capture of a variety of data points, including (but not limited to):

* **Real-time Telemetry:** Speed, RPM, current gear, throttle and brake inputs.
* **Lap Data:** Last lap time, best session lap, lap count.
* **Car Status:** Tire temperatures and pressures, fuel level, vehicle damage.
* **Session Info:** Track name, car used, weather conditions.
* _(Add other specific data points your scripts capture here!)_

Data can be saved to formats like CSV or JSON, or displayed in the console in real-time.

## 🚀 Getting Started

To use these scripts, you will need Python installed on your computer, as well as the target simulator.

### Prerequisites

* [Python 3.8+](https://www.python.org/downloads/)
* The simulator (iRacing or ACC) installed and running.
* Python libraries (see installation step below).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/racing4all.git
    cd racing4all
    ```
    *Replace `[YOUR_USERNAME]` with your GitHub username.*

2.  **Install dependencies:**
    It is highly recommended to create a virtual environment (`venv`) before installing dependencies.
    ```bash
    # (Optional, but recommended) Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install the required dependencies
    pip install -r requirements.txt
    ```
    

## 🛠️ How to Use

Each simulator has its own folder structure and scripts.

### For iRacing

1.  Navigate to the `iracing/` folder.
2.  Open iRacing and start a test session.
3.  Run the main acquisition script:
    ```bash
    python iracing_data_acq.py
    ```
4.  Data will be displayed in the console or saved to the output file specified in the script.

### For Assetto Corsa Competizione

1.  First, ensure the "Broadcast" option is enabled in ACC's settings menu.
2.  Navigate to the `acc/` folder.
3.  Open ACC and start a test session.
4.  Run the main acquisition script:
    ```bash
    python acc_data_acq.py
    ```



## 📁 Repository Structure

```
racing4all/
│
├── iracing/
│   ├── read_iracing.py     # Main script for iRacing
│   └── ...                     # Other files and modules
│
├── acc/
│   ├── read_acc.py         # Main script for ACC
│   └── ...                     # Other files and modules
│
├── LICENSE                     # Project's license file
└── README.md                   # This file
```



