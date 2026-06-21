from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser

class HelpDialog(QDialog):
    """
    A dialog window providing the user with an instructional guide on how to 
    operate the rPPG monitoring application and optimize capture conditions.
    """
    def __init__(self, parent=None):
        """
        Initializes the HelpDialog interface, applies styling, and sets the HTML content.
        """
        super().__init__(parent)
        self.setWindowTitle("User Guide")
        self.resize(650, 700) 
        
        # Modern dark theme styling matching the main app
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTextBrowser {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #585b70;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(False)
        
        # Clean HTML layout for the instructions
        help_html = """
        <h2 style='color: #89b4fa; text-align: center;'>Welcome to the VitalSign Monitoring System</h2>
        <p>This system enables contactless heart rate measurement through video analysis. Here is a quick guide on how to use it:</p>
        
        <h3 style='color: #a6e3a1;'>1. Selecting the Video Source</h3>
        <ul>
            <li><b>Video File:</b> Select this option from the dropdown menu, click <b>📂 Open</b> to choose a video, and then click <b>▶ Start</b>.</li>
            <li><b>Live Webcam:</b> Select this option, then click <b>▶ Start</b> directly. Sit steadily facing the camera and wait (at least 15-20 seconds recommended) so the system can gather enough data.</li>
        </ul>

        <h3 style='color: #a6e3a1;'>2. Stopping the Measurement & Results</h3>
        <p>When you wish to end the measurement, click <b>⏹ Stop</b>. The system will display the <b>Final Avg HR</b> – representing the stable median of the collected measurements.</p>

        <h3 style='color: #a6e3a1;'>3. Understanding the Charts</h3>
        <ul>
            <li><b>Heart Rate Plot (Top):</b> Displays real-time changes in your heart rate (BPM).</li>
            <li><b>Frequency Plot (Bottom):</b> Shows the frequency spectrum extracted from the facial blood flow. The highest peak represents the current heart rate frequency.</li>
        </ul>

        <h3 style='color: #a6e3a1;'>4. Sample Quality Indicator (Top Right)</h3>
        <p>In the top right corner, you will see a <b>Sample Quality</b> metric. This shows the real-time quality of the video capture in pixels, which directly affects the system's accuracy:</p>
        <ul>
            <li><b>Minimum Requirement:</b> The system requires at least <b>4,500 pixels</b>.</li>
            <li><b>Below 4,500:</b> The quality will display as <b>Bad</b>. You may need to move closer to the camera or improve your lighting.</li>
            <li><b>Above 4,500:</b> The quality gradually improves to <b>Good</b>, <b>Very Good</b>, or <b>Excellent</b>, ensuring the highest accuracy.</li>
        </ul>

        <hr style='border: 1px solid #45475a; margin: 15px 0;'>

        <h3 style='color: #f9e2af;'>⭐ Tips for the Best Results</h3>
        <ul>
            <li><b>Sit Close & Clear:</b> Ensure your forehead is fully visible. Please remove hats and brush aside any hair covering your forehead.</li>
            <li><b>Even Lighting:</b> Sit in a well-lit room with uniform ambient lighting. Avoid harsh, direct light or shadows on your face.</li>
            <li><b>Stay Still:</b> Remain as still as possible during the recording. Minor head movements or talking can introduce motion artifacts.</li>
            <li><b>Stable Camera:</b> Make sure your webcam is stable and stationary.</li>
        </ul>
        """
        text_browser.setHtml(help_html)
        layout.addWidget(text_browser)

        close_btn = QPushButton("Understood")
        close_btn.setFixedSize(120, 35)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)