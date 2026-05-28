Standalone client without server and without login.

Run:
    python client.py

Main behavior:
- Opens SpecificPatientScreen directly.
- Does not connect to a server.
- send_hr_to_server is disabled when client=None.

Required packages:
    pip install pyqt5 opencv-python numpy scipy pillow matplotlib

Optional:
    pip install mediapipe
