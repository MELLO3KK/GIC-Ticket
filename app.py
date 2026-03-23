import os
import uuid
import random
import qrcode
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Use a secure random key in production

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_CSV = os.path.join(BASE_DIR, 'users.csv')
TICKETS_CSV = os.path.join(BASE_DIR, 'tickets.csv')
QR_DIR = os.path.join(BASE_DIR, 'static', 'qrcodes')

if not os.path.exists(QR_DIR):
    os.makedirs(QR_DIR)

def generate_unique_token(df_users=None):
    while True:
        token = str(random.randint(100000000000, 999999999999)) # 12-digit numeric token
        if df_users is None or token not in df_users['token'].astype(str).values:
            return token

def init_db():
    if not os.path.exists(USERS_CSV):
        df_users = pd.DataFrame({
            'username': ['admin1', 'admin2', 'admin3', 'agent1', 'agent2'],
            'token': [generate_unique_token() for _ in range(5)],
            'role': ['admin', 'admin', 'admin', 'agent', 'agent'],
            'paid_amount': [0, 0, 0, 0, 0]
        })
        df_users.to_csv(USERS_CSV, index=False)
    
    if not os.path.exists(TICKETS_CSV):
        df_tickets = pd.DataFrame(columns=['id', 'student_name', 'class_name', 'agent_username', 'qr_token', 'qr_image'])
        df_tickets.to_csv(TICKETS_CSV, index=False)

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        token = request.form['token']
        
        df_users = pd.read_csv(USERS_CSV)
        # Ensure tokens are compared strictly as strings
        user = df_users[df_users['token'].astype(str) == str(token)]
        
        if not user.empty:
            session['username'] = user.iloc[0]['username']
            session['role'] = user.iloc[0]['role']
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('agent_dashboard'))
        else:
            flash('Invalid login token')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    df_tickets = pd.read_csv(TICKETS_CSV)
    return render_template('admin_dashboard.html', tickets=df_tickets.to_dict('records'))

@app.route('/agent', methods=['GET', 'POST'])
def agent_dashboard():
    if session.get('role') != 'agent':
        return redirect(url_for('login'))
        
    username = session['username']
    
    if request.method == 'POST':
        student_name = request.form['student_name']
        class_name = request.form['class_name']
        
        # Make ticket ID and secure token
        ticket_id = str(uuid.uuid4())[:8]
        qr_token = str(uuid.uuid4())
        qr_filename = f"{ticket_id}.png"
        qr_path = os.path.join(QR_DIR, qr_filename)
        
        # Generate QR Code image
        img = qrcode.make(qr_token)
        img.save(qr_path)
        
        df_tickets = pd.read_csv(TICKETS_CSV)
        new_ticket = pd.DataFrame([{
            'id': ticket_id,
            'student_name': student_name,
            'class_name': class_name,
            'agent_username': username,
            'qr_token': qr_token,
            'qr_image': qr_filename
        }])
        df_tickets = pd.concat([df_tickets, new_ticket], ignore_index=True)
        df_tickets.to_csv(TICKETS_CSV, index=False)
        flash('Ticket created successfully')
        return redirect(url_for('agent_dashboard'))
        
    df_tickets = pd.read_csv(TICKETS_CSV)
    my_tickets = df_tickets[df_tickets['agent_username'] == username]
    
    df_users = pd.read_csv(USERS_CSV)
    user_row = df_users[df_users['username'] == username]
    paid_amount = user_row.iloc[0].get('paid_amount', 0) if not user_row.empty else 0
    tickets_sold = len(my_tickets)
    total_value = tickets_sold * 25000
    amount_to_pay = total_value - paid_amount
    
    return render_template('agent_dashboard.html', tickets=my_tickets.to_dict('records'), amount_to_pay=amount_to_pay, tickets_sold=tickets_sold)

@app.route('/admin/delete/<ticket_id>')
def delete_ticket(ticket_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    df_tickets = pd.read_csv(TICKETS_CSV)
    
    ticket = df_tickets[df_tickets['id'] == ticket_id]
    if not ticket.empty:
        qr_image = ticket.iloc[0]['qr_image']
        qr_path = os.path.join(QR_DIR, qr_image)
        if os.path.exists(qr_path):
            os.remove(qr_path)
            
    df_tickets = df_tickets[df_tickets['id'] != ticket_id]
    df_tickets.to_csv(TICKETS_CSV, index=False)
    flash(f'Ticket {ticket_id} deleted')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<ticket_id>', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    df_tickets = pd.read_csv(TICKETS_CSV)
    
    if request.method == 'POST':
        student_name = request.form['student_name']
        class_name = request.form['class_name']
        
        df_tickets.loc[df_tickets['id'] == ticket_id, ['student_name', 'class_name']] = [student_name, class_name]
        df_tickets.to_csv(TICKETS_CSV, index=False)
        flash(f'Ticket {ticket_id} updated')
        return redirect(url_for('admin_dashboard'))
    
    ticket = df_tickets[df_tickets['id'] == ticket_id]
    if ticket.empty:
        flash('Ticket not found')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('edit_ticket.html', ticket=ticket.iloc[0].to_dict())

@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    df_users = pd.read_csv(USERS_CSV)
    df_tickets = pd.read_csv(TICKETS_CSV)
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        role = request.form['role'].strip()
        
        if username in df_users['username'].values:
            flash(f'Username "{username}" already exists!')
            return redirect(url_for('manage_users'))
            
        new_token = generate_unique_token(df_users)
        
        new_user = pd.DataFrame([{
            'username': username,
            'token': new_token,
            'role': role,
            'paid_amount': 0
        }])
        
        df_users = pd.concat([df_users, new_user], ignore_index=True)
        df_users.to_csv(USERS_CSV, index=False)
        flash(f'User "{username}" created successfully! Token: {new_token}')
        return redirect(url_for('manage_users'))
        
    users_data = []
    for _, user in df_users.iterrows():
        u_dict = user.to_dict()
        if u_dict['role'] == 'agent':
            t_sold = len(df_tickets[df_tickets['agent_username'] == u_dict['username']])
            u_dict['tickets_sold'] = t_sold
            u_dict['total_value'] = t_sold * 25000
            u_dict['paid_amount'] = u_dict.get('paid_amount', 0)
            u_dict['amount_to_pay'] = u_dict['total_value'] - u_dict['paid_amount']
        users_data.append(u_dict)
        
    return render_template('admin_users.html', users=users_data)

@app.route('/admin/payment/<username>', methods=['POST'])
def update_payment(username):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    df_users = pd.read_csv(USERS_CSV)
    if username not in df_users['username'].values:
        flash('User not found')
        return redirect(url_for('manage_users'))
        
    action = request.form.get('action')
    
    if action == 'clear':
        df_tickets = pd.read_csv(TICKETS_CSV)
        t_sold = len(df_tickets[df_tickets['agent_username'] == username])
        df_users.loc[df_users['username'] == username, 'paid_amount'] = t_sold * 25000
        flash(f'Payment cleared for {username}')
        
    elif action == 'edit':
        try:
            new_paid = int(request.form.get('paid_amount', 0))
            df_users.loc[df_users['username'] == username, 'paid_amount'] = new_paid
            flash(f'Payment updated for {username}')
        except ValueError:
            flash('Invalid amount entered')
            
    df_users.to_csv(USERS_CSV, index=False)
    return redirect(url_for('manage_users'))

if __name__ == '__main__':
    from waitress import serve
    print("Starting production server with Waitress on http://0.0.0.0:5000...")
    serve(app, host='0.0.0.0', port=5000, threads=10)
