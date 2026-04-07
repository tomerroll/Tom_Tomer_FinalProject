# Heart Rate Extraction Application

## Overview
Welcome to Heart Rate Extraction Application, a client-server desktop application developed in Python for extracting heart rates from patients using recorded or live video. The application features a user-friendly UI to manage patient and user data, stored efficiently in JSON data files. The heart rate extraction process involves a sophisticated pipeline, outlined below.

## Pipeline for Heart Rate Extraction
**1. Receiving Video Input:**
- Handling both recorded and live video streams at 30 Hz, 1920x1080 resolution.

**2. Locating the Eyes Using Haar Cascade Classifier**
- Employing Haar cascade classifier to precisely identify eyes in video frames.

**3. Locating the Region of Interest (ROI)**
- Selecting the forehead as the ROI post eye detection, leveraging its suitability for pulse detection.

**4. Addressing the Green Color Channel**
- Converting ROI to RGB, isolating the green channel, and applying median calculation for noise reduction.

**5. Performing FFT**
- Applying Fast Fourier Transform on the green channel data to transition from time domain to frequency domain, enhancing signal clarity by adjusting sample size.

**6. Calculating Absolute FFT Values**
- Deriving absolute values from the FFT output to process frequency components effectively.

**7. Calculating Heart Rate Thresholds**
- Determining low and high heart rate thresholds to identify potential heart rate frequencies based on FFT analysis.

**8. Searching for the Highest Value in Threshold Range**
- Identifying the peak frequency within the calculated heart rate thresholds indicative of the actual heart rate.

**9. Calculating the Heart Rate Frequency**
- Using the peak frequency to calculate the heart rate frequency with a refined formula.

**10. Calculating the Heart Rate**
- Converting heart rate frequency to beats per minute (BPM) to determine the patient's heart rate.
   
## References
Our development process and pipeline for extracting the pulse were influenced and guided by valuable insights from the following articles:

1.	Bush, I. (2016). Measuring Heart Rate from Video. Stanford Computer Science.
2.	Hill, B. L., Liu, X., McDuff, D. (2021). Beat-to-Beat Cardiac Pulse Rate Measurement From Video. University of California, Los Angeles.
3.	Lee, Y. C., Syakura, A., Khalil, M. A., Wu, C. H., Ding, Y. F., Wang, C. W. (September 2020). A real-time camera-based adaptive breathing monitoring system.
4.	Molinaro, N., Schena, E., Silvestri, S., Bonotti, F., Aguzzi, D., Viola, E., Buccolini, F., Massaroni, C. (February 2022). Contactless Vital Signs Monitoring From Videos Recorded With Digital Cameras: An Overview.
5.	Viola, P., Jones, M. (2001). Rapid Object Detection using a Boosted Cascade of Simple Features. Mitsubishi Electric Research Labs, Compaq CRL.
6.	Chen, X., Cheng, J., Song, R., Liu, Y., Ward, R., Wang, Z. J. (October 2019). Video-Based Heart Rate Measurement: Recent Advances and Future Prospects.
