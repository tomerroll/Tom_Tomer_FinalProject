import sys
from PyQt5.QtWidgets import QApplication
from specificPatientScreen import SpecificPatientScreen

DEFAULT_PATIENT_ID = 1

def main():
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
