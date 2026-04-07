import socket
import threading
import json

IP = socket.gethostbyname(socket.gethostname())
PORT = 5000
ADDR = (IP, PORT)
active_client = None  # Initialize active client as None
heart_rate1 = 0
heart_rate2 = 0
heart_rate3 = 0
frame1 = 0
frame2 = 0
frame3 = 0
num = "0"


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.", end="")
    global active_client  # Reference the global active_client variable
    global heart_rate1
    global heart_rate2
    global heart_rate3
    global frame1
    global frame2
    global frame3
    global num
    connected = True
    current_user = None  # Track the current user

    # While client is connected to the server
    while connected:
        msg = conn.recv(1024).decode("utf-8")
        # ************************************* Queries ******************************************* #
        # If the user disconnected from the app
        if msg == 'DISCONNECT':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)

            print(f"{addr} disconnected.")

            # Reset loggedIn status to 0 for the current user
            if current_user is not None:
                user = next((user for user in data['users'] if user['username'] == current_user), None)
                if user is not None:
                    user['loggedIn'] = "0"

                # Write the updated data back to the db.json file
                with open('db.json', 'w') as file:
                    json.dump(data, file, indent=4, sort_keys=True)

            break

        # Verify the login when user insert username and password
        elif msg == 'LOGIN_REQUEST':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)

            # Receive the login data from the client
            login_data = conn.recv(1024).decode("utf-8")
            login_data = json.loads(login_data)

            # Verify the login credentials
            username = login_data['username']
            password = login_data['password']
            login_successful = False

            for user in data['users']:
                if user['username'] == username and user['password'] == password:
                    if user['loggedIn'] == "1":  # User already logged in
                        login_successful = "alreadyLoggedIn"
                    else:  # Login successful
                        login_successful = True
                        user['loggedIn'] = "1"
                        current_user = username  # Set the current user
                        # Write the updated data back to the db.json file
                        with open('db.json', 'w') as file:
                            json.dump(data, file, indent=4, sort_keys=True)
                    break
            # Send the login result to the client
            conn.send(str(login_successful).encode("utf-8"))

        # Update DB with updated patients list
        elif msg == 'UPDATE_PATIENTS_REQUEST':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)

            # Receive the patient data from the client
            patients_data = conn.recv(1024).decode("utf-8")
            patients_data = json.loads(patients_data)

            # Update the database with the updated patients list
            data['patients'] = patients_data

            # Write the updated data back to the db.json file
            with open('db.json', 'w') as file:
                json.dump(data, file, indent=4, sort_keys=True)

        # Update the DB with new patient
        elif msg == 'ADD_PATIENT_REQUEST':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)

            # Receive the patient data from the client
            patient_data = conn.recv(1024).decode("utf-8")
            patient_data = json.loads(patient_data)

            # Check if the patient ID already exists
            patient_id = patient_data['id']
            patient_exists = any(patient['id'] == patient_id for patient in data['patients'])
            id_exist = False

            # If the patient ID already exists, send True to the client
            if patient_exists:
                id_exist = True
                conn.send(str(id_exist).encode("utf-8"))
            else:
                # Update the database with the new patient data by adding him to the patients list
                data['patients'].append(patient_data)

                # Write the updated data back to the db.json file
                with open('db.json', 'w') as file:
                    json.dump(data, file, indent=4, sort_keys=True)

                # Send False to the client indicating the update was successful
                conn.send(str(id_exist).encode("utf-8"))

        # Send the patients buttons states
        elif msg == 'GET_BUTTON_STATES':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)
                button_states = data['patientsButtons']
                json_data = json.dumps(button_states)  # Convert to JSON string
                conn.send(json_data.encode("utf-8"))  # Send the encoded JSON string

        # Update the patients buttons states
        elif msg == 'UPDATE_BUTTON_STATES':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)

            # Receive the patient data from the client
            patient_data = conn.recv(1024).decode("utf-8")
            patient_data = json.loads(patient_data)

            # Update the corresponding button state
            button_id = patient_data['id']
            enabled = patient_data['enabled']

            for state in data['patientsButtons']:
                if state['id'] == button_id:
                    state['enabled'] = enabled
                    break

            # Save the updated data back to the db.json file
            with open('db.json', 'w') as file:
                json.dump(data, file, indent=4, sort_keys=True)

        # Query that checks if there is another client on the Panel Screen page
        elif msg == 'ENTER_PANEL_SCREEN':
            if active_client is None:  # If there is no one on the panel screen
                active_client = conn  # Set the current client as the active client
                # Send the response to the client allowing entry
                conn.send('ENTRY_ALLOWED'.encode("utf-8"))
            else:
                # Send the response to the client denying entry
                conn.send('ENTRY_DENIED'.encode("utf-8"))

        # Query that indicate that there is no one on the panel screen after navigate from there to another screen
        elif msg == 'LEAVE_PANEL_SCREEN':
            active_client = None  # Reset the active client when they leave the panel screen

        # Read from the db and send the updated patients that have been added to the system
        elif msg == 'GET_PATIENTS_DATA':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)
                patients = data['patients']
                json_data = json.dumps(patients)  # Convert to JSON string
                conn.send(json_data.encode("utf-8"))  # Send the encoded JSON string

        # Read from the db and send the updated patients that get treatment
        elif msg == 'GET_PATIENTS_IN_TREATMENT_DATA':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)
                patients = data['patientsInTreatment']
                json_data = json.dumps(patients)  # Convert to JSON string
                conn.send(json_data.encode("utf-8"))  # Send the encoded JSON string

        # Update the db of patients that get treatment
        elif msg == 'UPDATE_PATIENTS_IN_TREATMENT_DATA':
            # Read the updated data from the db.json
            with open('db.json', 'r') as file:
                data = json.load(file)

            # Receive the patient data from the client
            patient_data = conn.recv(1024).decode("utf-8")
            patient_data = json.loads(patient_data)

            # Check the num of the patient data and then update it based on it
            num = patient_data['patient']

            # Find the index of the patient with the matching "patient" number in the "patientsInTreatment" array
            index = None
            for i, patient in enumerate(data['patientsInTreatment']):
                if patient['patient'] == num:
                    index = i
                    break

            # If the patient is found, update the corresponding entry with the new patient data
            if index is not None:
                data['patientsInTreatment'][index]['firstName'] = patient_data['firstName']
                data['patientsInTreatment'][index]['lastName'] = patient_data['lastName']
            else:
                # If the patient is not found, it's a new patient,
                # so append the new patient data to the "patientsInTreatment" array
                data['patientsInTreatment'].append(patient_data)

            # Write the updated data back to the db.json file
            with open('db.json', 'w') as file:
                json.dump(data, file, indent=4, sort_keys=True)

        # Handle the heart rate update from the specific Patient screen
        elif msg == 'HEART_RATE_UPDATE':
            # Receive the heart rate data from the client
            data = conn.recv(1024).decode("utf-8")
            data = json.loads(data)

            # num is the number of the patient (1/2/3 in our case)
            if data['num'] == "1":
                heart_rate1 = data['heart_rate']
            if data['num'] == "2":
                heart_rate2 = data['heart_rate']
            if data['num'] == "3":
                heart_rate3 = data['heart_rate']

        # Send to the panel screen the updated hear rate of the patients
        elif msg == 'GET_HEART_RATE':
            response_data = {
                "heart_rate1": heart_rate1,
                "heart_rate2": heart_rate2,
                "heart_rate3": heart_rate3
            }
            json_data = json.dumps(response_data)
            conn.send(json_data.encode("utf-8"))

    conn.close()
    # If User disconnected, print the updated active connections
    print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")


def main():
    print("[STARTING] Server is starting...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"[LISTENING] Server is listening on {IP}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"\n[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


if __name__ == "__main__":
    main()
