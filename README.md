# GIC Ticket & Attendance System

A Flask-based web application for managing school ticket sales and student attendance.

## Features

### Dual Roles
- **Admin**: Full dashboard for managing tickets, users (Agents), attendance logs, and student check-ins/outputs.
- **Agent**: Dashboard for selling tickets to students, tracking personal sales, and viewing payment status.

### Ticket Generation & QR Codes
- **Branded QR Codes**: Tickets automatically generate unique UUID-based QR codes embedded into a custom design template (`template.jpg`) for a professional look.
- **Smart Naming Convention**: QR code downloads are automatically named using the `<student_name>_<class>` format.
- **Agent Tracking**: Each ticket records which agent sold it for accurate sales management.

### Attendance Management
- **Integrated Check-in/Check-out**: High-speed scanner-ready interface for checking students in and out.
- **Duplicate Prevention**: Built-in logic to prevent double check-ins and ensure students are checked in before check-out is possible.
- **Real-time Attendance Logs**: View all entries and exits in a chronological log.
- **Not-Checked-In List**: Quickly identify students who have purchased tickets but hasn't entered the venue.

### Data Management & Exports
- **CSV Data Export**: Admins and Agents can export data (Tickets, Attendance, Not-Checked-In lists) to CSV for external record keeping.
- **Agent Management**: Admins can track agent sales value, total paid amount, amount to pay, and toggle ticket selling permissions for individual agents or globally.

### Design
- **Premium Aesthetics**: Professional gold and black theme tailored for school events and gala atmospheres.

## Tech Stack
- **Backend**: [Flask](https://flask.palletsprojects.com/)
- **Database**: [Supabase](https://supabase.com/)
- **Production Server**: [Waitress](https://docs.pylonsproject.org/projects/waitress/)
- **QR Processing**: [Pillow](https://python-pillow.org/)

## Environment Setup Instructions

Follow these steps to set up and run the application locally.

1. **Open a terminal** and navigate to this project folder.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
4. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the Application**:
   ```bash
   python app.py
   ```
6. **Access the application**: Open your web browser and go to `http://127.0.0.1:5000`
