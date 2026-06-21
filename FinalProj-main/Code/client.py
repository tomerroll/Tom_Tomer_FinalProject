import sys
from PyQt5.QtWidgets import QApplication
from specificPatientScreen import SpecificPatientScreen

DEFAULT_PATIENT_ID = 1

def main():
    """
    Main application entry point. Initializes the underlying PyQt5 framework, 
    instantiates the SpecificPatientScreen, and executes the event loop.
    """
    app = QApplication(sys.argv)

    window = SpecificPatientScreen(
        app=app,
        client=None,
        patient=DEFAULT_PATIENT_ID,
        main_window=None
    )

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()