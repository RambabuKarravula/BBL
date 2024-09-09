import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import time
import qrcode
import os
import uuid
from PIL import Image
import cv2
from pyzbar.pyzbar import decode
import base64

# Define the Excel file paths
excel_file_form1 = "Detect Record(Coloring).xlsx"
excel_file_form2 = "Defect Record (QA).xlsx"
excel_file_form3 = "History Record(Washing).xlsx"
EXCEL_FILE = "user_data.xlsx"

# Define dropdown options for the columns in both forms
shift_options = ["A", "B", "C"]
grade_options = ["A", "B", "C", "D"]
operator_name_options = ["R.Dinesh", "Shrinnivisan", "Rambabu"]
part_number_options = ["12345-74L10", "23456-85M20", "34567-96N30"]

# Folder to store QR codes
QR_FOLDER = "qr_codes"
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)

# Helper function to generate a QR code
def generate_qr_code(user_email):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(user_email)  # Using email as the unique identifier
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")

    # Save QR code as PNG
    file_path = os.path.join(QR_FOLDER, f"{user_email}.png")
    img.save(file_path)
    return file_path

# Helper function to download the QR code
def get_image_download_link(img_path):
    with open(img_path, "rb") as f:
        img_data = f.read()
    b64_img = base64.b64encode(img_data).decode("utf-8")
    href = f'<a href="data:file/png;base64,{b64_img}" download="{os.path.basename(img_path)}">Download QR Code</a>'
    return href

# Helper function to save user data in Excel
def save_user_data_to_excel(data):
    try:
        # Check if the file already exists
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
        else:
            df = pd.DataFrame(columns=['Name', 'Username', 'Email', 'Phone Number'])

        # Append the new data
        new_row = pd.DataFrame(data, columns=['Name', 'Username', 'Email', 'Phone Number'])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save back to the Excel file
        df.to_excel(EXCEL_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving to Excel: {e}")
        return False

# Helper function to decode a QR code from a frame
def decode_qr_code_from_frame(frame):
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        return obj.data.decode('utf-8')
    return None

# Function to get the next serial number
def get_next_serial_number(excel_file):
    try:
        df = pd.read_excel(excel_file)
        last_serial_number = df['Serial Number'].max()
        return last_serial_number + 1
    except (FileNotFoundError, KeyError):
        return 1  # Start from 1 if file doesn't exist or column is missing

# Page for user registration
def registration_page():
    st.title("User Registration")

    with st.form("registration_form"):
        name = st.text_input("Name")
        username = st.text_input("Username")
        email = st.text_input("Email")
        phone_number = st.text_input("Phone Number")
        submitted = st.form_submit_button("Register")

        if submitted:
            if not (name and username and email and phone_number):
                st.error("Please fill out all fields")
            else:
                # Save user details to Excel
                user_data = [[name, username, email, phone_number]]
                if save_user_data_to_excel(user_data):
                    # Generate the QR code for the user
                    qr_code_path = generate_qr_code(email)
                    st.success("Registration successful!")
                    st.image(qr_code_path, caption="Your QR Code")
                    st.markdown(get_image_download_link(qr_code_path), unsafe_allow_html=True)
                    st.info("Please save your QR code. You'll need it to log in.")
                    if st.button("Proceed to Login"):
                        st.session_state.page = 'login'
                        st.rerun()

# Page for user login using camera
def login_page():
    st.title("QR Code Login")

    # Access the webcam feed using OpenCV
    cap = cv2.VideoCapture(0)  # 0 for the primary camera

    if not cap.isOpened():
        st.error("Could not access the camera.")
        return

    st.info("Scanning for QR code. Please show your QR code to the camera.")
    
    # Frame placeholder for the live camera feed in Streamlit
    frame_placeholder = st.empty()

    try:
        while True:
            ret, frame = cap.read()  # Read the camera frame
            if not ret:
                st.error("Failed to capture the frame.")
                break

            # Decode the QR code from the current frame
            decoded_data = decode_qr_code_from_frame(frame)

            # Show the camera feed
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
            frame_placeholder.image(frame, channels="RGB")

            # If a QR code is detected, stop the loop and log the user in
            if decoded_data:
                # Verify the user exists in the Excel file
                df = pd.read_excel(EXCEL_FILE)
                if decoded_data in df['Email'].values:
                    st.success(f"Login successful! Welcome, {decoded_data}")
                    st.session_state.logged_in = True
                    st.session_state.user_email = decoded_data
                    break
                else:
                    st.error("User not found. Please register first.")
                    break

    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        # Release the camera after use
        cap.release()

    if st.session_state.logged_in:
        st.rerun()

# Home Page
def home_page():
    st.markdown("""
        <style>
        .header {
            text-align: center;
            margin-top: 20px;
        }
        .button-container {
            text-align: center;
            margin-top: 20px;
        }
        </style>
        <div class="header">
            <h1>Welcome to BBL DAIDO PRIVATE LIMITED</h1>
            <p>(A MEMBER OF DAIDO METAL & AMALGAMATIONS GROUP).</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    if st.button("Get Started"):
        st.session_state.page = 'signup_login'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Signup and Login Page
def signup_login_page():
    st.title("Sign Up or Log In")
    choice = st.radio("Choose an option:", ["Sign Up", "Log In"])
    
    if choice == "Sign Up":
        registration_page()
    else:
        if st.button("Proceed to Login"):
            st.session_state.page = 'login'
            st.rerun()

# Main Page
def main_page():
    # Display the logged-in user's username at the top
    if 'user_email' in st.session_state:
        st.write(f"Logged in as: {st.session_state.user_email}")
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a Page", ["Detect Record (Coloring)", "Defect Record (QA)", "History Record (Washing)", "Search Data"])
    
    if page == 'Detect Record (Coloring)':
        detect_record_coloring()
    elif page == 'Defect Record (QA)':
        defect_record_qa()
    elif page == 'History Record (Washing)':
        history_record_washing()
    elif page == 'Search Data':
        search_data()

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.page = 'home'
        st.rerun()

# Detect Record (Coloring) Form
def detect_record_coloring():
    st.header("Detect Record (Coloring)")
    with st.form("detect_record_coloring_form"):
        serial_no = get_next_serial_number(excel_file_form1)
        st.text(f"Serial Number: {serial_no}")
        date = datetime.date.today()
        shift = st.selectbox("SHIFT", shift_options)
        job_no = st.text_input("JOB NO")
        part_number = st.selectbox("Part Number", part_number_options)
        grade = st.selectbox("Grade", grade_options)
        before_qty = st.number_input("Before QTY", min_value=0)
        c57c = st.number_input("C57c", min_value=0)
        c88 = st.number_input("C88", min_value=0)
        c87a = st.number_input("C87a", min_value=0)
        c87b = st.number_input("C87b", min_value=0)
        operator_name = st.selectbox("Operator Name", operator_name_options)
        ok_qty = st.number_input("OK QTY", min_value=0)
        ng_total = st.number_input("NG Total (Auto)", min_value=0)
        day_of_week = st.selectbox("Day of week", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        unknown = st.text_input("Unknown")
        line = st.text_input("Line")

        submit_button = st.form_submit_button(label="Submit Data")

    if submit_button:
        new_entry = {
            "Serial Number": serial_no,
            "DATE": date,
            "SHIFT": shift,
            "JOB NO": job_no,
            "Part Number": part_number,
            "Grade": grade,
            "Before QTY": before_qty,
            "C57c": c57c,
            "C88": c88,
            "C87a": c87a,
            "C87b": c87b,
            "Operator Name": operator_name,
            "OK QTY": ok_qty,
            "NG Total (Auto)": ng_total,
            "Day of week": day_of_week,
            "Unknown": unknown,
            "Line": line
        }

        try:
            df = pd.read_excel(excel_file_form1)
        except FileNotFoundError:
            df = pd.DataFrame(columns=[
                "Serial Number", "DATE", "SHIFT", "JOB NO", "Part Number", "Grade", 
                "Before QTY", "C57c", "C88", "C87a", "C87b", "Operator Name", 
                "OK QTY", "NG Total (Auto)", "Day of week", "Unknown", "Line"
            ])
        
        new_entry_df = pd.DataFrame([new_entry])
        df = pd.concat([df, new_entry_df], ignore_index=True)
        df.to_excel(excel_file_form1, index=False)

        success_placeholder = st.empty()
        success_placeholder.success("Data for Detect Record (Coloring) has been saved successfully!")
        time.sleep(2)
        success_placeholder.empty()

        st.rerun()

# Defect Record (QA) Form
def defect_record_qa():
    st.header("Defect Record (QA)")
    with st.form("defect_record_qa_form"):
        serial_no = get_next_serial_number(excel_file_form2)
        st.text(f"Serial Number: {serial_no}")
        date = datetime.date.today()
        
        shift = st.selectbox("SHIFT", shift_options)
        job_no = st.text_input("JOB NO")
        part_name = st.text_input("Part Name")
        supplier = st.text_input("Supplier")
        location = st.text_input("Location")
        machine_no = st.text_input("Machine No")
        program_no = st.text_input("Program No")
        ok_qty = st.number_input("OK QTY", min_value=0)
        ng_qty = st.number_input("NG QTY", min_value=0)
        rework_qty = st.number_input("Rework QTY", min_value=0)
        rejection_reason = st.text_input("Rejection Reason")
        operator_name = st.selectbox("Operator Name", operator_name_options)

        submit_button = st.form_submit_button(label="Submit Data")

    if submit_button:
        new_entry = {
            "Serial Number": serial_no,
            "DATE": date,
            "SHIFT": shift,
            "JOB NO": job_no,
            "Part Name": part_name,
            "Supplier": supplier,
            "Location": location,
            "Machine No": machine_no,
            "Program No": program_no,
            "OK QTY": ok_qty,
            "NG QTY": ng_qty,
            "Rework QTY": rework_qty,
            "Rejection Reason": rejection_reason,
            "Operator Name": operator_name
        }

        try:
            df = pd.read_excel(excel_file_form2)
        except FileNotFoundError:
            df = pd.DataFrame(columns=[
                "Serial Number", "DATE", "SHIFT", "JOB NO", "Part Name", "Supplier", 
                "Location", "Machine No", "Program No", "OK QTY", "NG QTY", 
                "Rework QTY", "Rejection Reason", "Operator Name"
            ])
        
        new_entry_df = pd.DataFrame([new_entry])
        df = pd.concat([df, new_entry_df], ignore_index=True)
        df.to_excel(excel_file_form2, index=False)

        success_placeholder = st.empty()
        success_placeholder.success("Data for Defect Record (QA) has been saved successfully!")
        time.sleep(2)
        success_placeholder.empty()
        st.rerun()

# History Record (Washing) Form
def history_record_washing():
    st.header("History Record (Washing)")
    with st.form("history_record_washing_form"):
        serial_no = get_next_serial_number(excel_file_form3)
        st.text(f"Serial Number: {serial_no}")
        date = datetime.date.today()
        
        shift = st.selectbox("SHIFT", shift_options)
        part_name = st.text_input("Part Name")
        washing_machine = st.text_input("Washing Machine")
        wash_time = st.time_input("Wash Time", value=datetime.datetime.now().time())
        operator_name = st.selectbox("Operator Name", operator_name_options)
        wash_qty = st.number_input("Wash QTY", min_value=0)

        submit_button = st.form_submit_button(label="Submit Data")

    if submit_button:
        new_entry = {
            "Serial Number": serial_no,
            "DATE": date,
            "SHIFT": shift,
            "Part Name": part_name,
            "Washing Machine": washing_machine,
            "Wash Time": wash_time,
            "Operator Name": operator_name,
            "Wash QTY": wash_qty
        }

        try:
            df = pd.read_excel(excel_file_form3)
        except FileNotFoundError:
            df = pd.DataFrame(columns=[
                "Serial Number", "DATE", "SHIFT", "Part Name", "Washing Machine", 
                "Wash Time", "Operator Name", "Wash QTY"
            ])
        
        new_entry_df = pd.DataFrame([new_entry])
        df = pd.concat([df, new_entry_df], ignore_index=True)
        df.to_excel(excel_file_form3, index=False)

        success_placeholder = st.empty()
        success_placeholder.success("Data for History Record (Washing) has been saved successfully!")
        time.sleep(2)
        success_placeholder.empty()

        st.rerun()

# Search Data
def search_data():
    st.header("Search Data")
    
    excel_file = st.selectbox("Select Excel File", ["Detect Record(Coloring)", "Defect Record (QA)", "History Record(Washing)"])

    file_paths = {
        "Detect Record(Coloring)": excel_file_form1,
        "Defect Record (QA)": excel_file_form2,
        "History Record(Washing)": excel_file_form3
    }
    
    selected_file_path = file_paths[excel_file]

    try:
        df = pd.read_excel(selected_file_path)
        columns = df.columns.tolist()
    except FileNotFoundError:
        st.error("Selected file not found.")
        return
    
    if 'DATE' in columns:
        selected_date = st.date_input("Select Date", value=datetime.date.today())
        
        df['DATE'] = pd.to_datetime(df['DATE']).dt.date
        
        filtered_df = df[df['DATE'] == selected_date]
    else:
        st.error("No DATE column found in the selected file.")
        return
    
    st.subheader(f"Data for {selected_date}")
    if not filtered_df.empty:
        st.dataframe(filtered_df)
    else:
        st.write("No records found for the selected date.")

# Initialize session state
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

# Main app function to switch between pages
def main():
    init_session_state()
    
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'signup_login':
        signup_login_page()
    elif st.session_state.page == 'login':
        if not st.session_state.logged_in:
            login_page()
        else:
            st.session_state.page = 'main'
            st.rerun()
    elif st.session_state.page == 'main':
        if st.session_state.logged_in:
            main_page()
        else:
            st.session_state.page = 'login'
            st.rerun()

# Run the main app
if __name__ == "__main__":
    main()