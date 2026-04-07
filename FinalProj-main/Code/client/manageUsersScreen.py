from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QFile, QTextStream
import json


# This Class is responsible for the Manage Menu Screen and its functionality
class ManageUsersScreen(QWidget):
    def __init__(self, app, client):
        super().__init__()
        self.app = app
        self.client = client
        self.window_menu_screen = None
        self.setWindowTitle('Monitoring Heart Rate Application')
        self.resize(1500, 800)  # Set the window size
        self.patients_data = None

        # Load and apply the CSS styles from the style.css file
        style_file = QFile('style.css')
        if style_file.open(QFile.ReadOnly | QFile.Text):
            style_stream = QTextStream(style_file)
            app.setStyleSheet(style_stream.readAll())

        # Back button
        back_button = QPushButton('Back', self)
        back_button.move(10, 10)  # Adjust the position of the back button
        back_button.clicked.connect(self.back_clicked)  # Connect the button's clicked signal to the go_back method
        back_button.setObjectName('back_button')  # set object name for using it in the css file

        # Save Button
        save_button = QPushButton('Save', self)
        save_button.move(520, 700)  # x,y coordinates value from top-left corner
        save_button.clicked.connect(self.save_clicked)

        # Delete Button
        delete_button = QPushButton('Delete', self)
        delete_button.move(760, 700)  # x,y coordinates value from top-left corner
        delete_button.clicked.connect(self.delete_selected_row)

        # Error label
        self.error_label = QLabel('', self)
        self.error_label.move(580, 630)  # x,y coordinates value from top-left corner
        self.error_label.setObjectName('error_label')  # set object name for using it in the css file
        self.error_label.setFixedSize(400, 40)  # Adjust width and height accordingly

        # Table to display patients' data
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['ID', 'First Name', 'Last Name'])
        self.table.setGeometry(480, 100, 510, 500)

        # Call the function to receive and display patients' data
        self.receive_and_display_patients_data()

        # Set up editing related signals
        self.table.itemChanged.connect(self.item_edited)

    # Go back to the previous window
    def back_clicked(self):
        from menuScreen import MenuScreen
        self.window_menu_screen = MenuScreen(self.app, self.client)
        self.window_menu_screen.show()
        self.hide()

    # Function that receives the patients' data
    def receive_and_display_patients_data(self):
        # Send the request for patients' data
        self.client.send('GET_PATIENTS_DATA'.encode('utf-8'))
        # Receive the data from the server and decode it
        received_data = self.client.recv(1024).decode('utf-8')
        # Parse the received data into a list of patients' information
        self.patients_data = json.loads(received_data)

        # Display the data in the table
        self.display_data_in_table()

    def display_data_in_table(self):
        if self.patients_data:
            self.table.setRowCount(len(self.patients_data))

            for row, patient in enumerate(self.patients_data):
                id_item = QTableWidgetItem(patient['id'])
                first_name_item = QTableWidgetItem(patient['firstName'])
                last_name_item = QTableWidgetItem(patient['lastName'])

                self.table.setItem(row, 0, id_item)
                self.table.setItem(row, 1, first_name_item)
                self.table.setItem(row, 2, last_name_item)

                self.table.setEditTriggers(QTableWidget.AnyKeyPressed | QTableWidget.DoubleClicked)

    # This method is called when an item in the table is edited
    def item_edited(self, item):
        row = item.row()
        column = item.column()
        edited_value = item.text()

        # update the data structure
        self.patients_data[row][['id', 'firstName', 'lastName'][column]] = edited_value

    # Triggered when save button clicked
    def save_clicked(self):
        # Check if any element in the array has an empty value for any key
        empty_found = any(not value for item in self.patients_data for value in item.values())
        if empty_found:
            self.error_label.setText('At least one of the fields are empty')
            self.error_label.show()
            return

        # Track seen IDs
        seen_ids = set()
        # Check if any element in the array has an ID that has already been seen
        id_already_exist = any(item['id'] in seen_ids or seen_ids.add(item['id']) for item in self.patients_data)
        if id_already_exist:
            self.error_label.setText('At least one element has an ID that already exists')
            self.error_label.show()
            return

        # Hide the previous error label
        self.error_label.hide()

        # Send a 'update patients request' to the server
        self.client.send('UPDATE_PATIENTS_REQUEST'.encode("utf-8"))
        # Send the patients data to the server
        self.client.send(json.dumps(self.patients_data).encode("utf-8"))
        self.error_label.setText('Changes have been saved')
        self.error_label.show()

    # Triggered when delete button clicked
    def delete_selected_row(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)

        # Check if there are selected rows
        if len(selected_rows) == 0:
            self.error_label.setText('Please select at least one row to delete')
            self.error_label.show()
            return

        # Hide the previous error label
        self.error_label.hide()

        for row in selected_rows:
            self.table.removeRow(row)
            del self.patients_data[row]
