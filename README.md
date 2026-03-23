# Ticket Selling System

A Flask-based web application for managing school ticket sales with Admin and Agent roles.

## Environment Setup Instructions

Follow these steps to set up and run the application locally on your machine.

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
6. **Access the application**: Open your web browser and go to http://127.0.0.1:5000

### Default Accounts

The database (`users.csv` and `tickets.csv`) will automatically initialize with the following predefined accounts on its first run:

**Admin Accounts (Full CRUD access on all tickets):**
* `admin1` (Login Token: `admin-token-1`)
* `admin2` (Login Token: `admin-token-2`)
* `admin3` (Login Token: `admin-token-3`)

**Agent Accounts (Can only create and view their own tickets):**
* `agent1` (Login Token: `agent-token-1`)
* `agent2` (Login Token: `agent-token-2`)

### Features
* **Authentication**: Token/Session handling using Flask's secure session capabilities and hashed passwords (via `werkzeug.security`).
* **Database**: Uses local Pandas DataFrames backed by `users.csv` and `tickets.csv`.
* **QR Codes**: Every generated ticket automatically produces a unique UUID secure token embedded into a QR code. The codes are stored inside `/static/qrcodes/`.
