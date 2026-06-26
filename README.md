# VitalSign Monitoring System

A standalone desktop application for contactless heart-rate estimation using rPPG facial video analysis.

## Overview

The system estimates heart rate from either a live webcam stream or a prerecorded video file.

The application detects the user's face, extracts the forehead Region of Interest (ROI), analyzes RGB color changes, and displays the estimated heart rate in real time.

No login or server connection is required.

## Main Features

- Live webcam heart-rate estimation
- Video file analysis
- Face detection
- Forehead ROI extraction
- Real-time BPM display
- Frequency display
- Final average heart-rate display
- Heart-rate graph
- FFT graph
- Sample quality indicator
- Help button with usage instructions

## Technologies Used

- Python
- PyQt5
- OpenCV
- NumPy
- SciPy
- Matplotlib
- Pillow

## Recommended Python Version

Use Python 3.11.

Python 3.13 is not recommended for this project because some packages may fail during installation.

## Setup Virtual Environment

Open PowerShell inside the project folder:

```powershell
cd /path/to/Tom_Tomer_FinalProject/Code
```

Create a virtual environment using Python 3.11:

```powershell
py -3.11 -m venv venv
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Check that the virtual environment uses Python 3.11:

```powershell
python --version
```

Install the required packages:

```powershell
pip install -r .\Requirements\requirements.txt
```

## Run the Project

Make sure the virtual environment is activated, then run:

```powershell
python client.py
```

## How to Use

### Video File

1. Select `Video File`.
2. Click `Open`.
3. Choose an MP4 or AVI file.
4. Click `Start`.
5. Click `Stop` when finished.

### Live Webcam

1. Select `Live Webcam`.
2. Wait for the webcam preview.
3. Sit in front of the camera.
4. Make sure your forehead is visible.
5. Click `Start`.
6. Click `Stop` when finished.

## Help Button

The application includes a `Help` button.

The Help window explains how to use the system, understand the graphs, and improve sample quality.

## Recommended Conditions

For better accuracy:

- Keep the forehead visible.
- Sit still during the measurement.
- Use stable indoor lighting.
- Avoid strong shadows or reflections.
- Keep the camera stable.
- Avoid talking during the measurement.

## Notes

This project is intended for academic and research purposes only.

It is not a medical device and should not be used for medical diagnosis.

## Authors

Tomer Roll  
Tom Biton

## Supervisors

Dr. Dan Lemberg  
Mrs. Elena Kramer


