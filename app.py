import os
import uuid
import random
import qrcode
from flask import Flask, render_template, request, redirect, url_for, session, flash
import db

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Use a secure random key in production

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_DIR = os.path.join(BASE_DIR, 'static', 'qrcodes')

if not os.path.exists(QR_DIR):
    os.makedirs(QR_DIR)


def generate_unique_token():
    existing_tokens = db.get_all_tokens()
    while True:
        token = str(random.randint(100000000000, 999999999999))  # 12-digit numeric token
        if token not in existing_tokens:
            return token


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        token = request.form['token']
        user = db.get_user_by_token(token)

        if user:
            session['username'] = user['username']
            session['role'] = user['role']
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

    tickets = db.get_all_tickets()
    return render_template('admin_dashboard.html', tickets=tickets)


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

        db.create_ticket({
            'id': ticket_id,
            'student_name': student_name,
            'class_name': class_name,
            'agent_username': username,
            'qr_token': qr_token,
            'qr_image': qr_filename,
        })
        flash('Ticket created successfully')
        return redirect(url_for('agent_dashboard'))

    my_tickets = db.get_tickets_by_agent(username)
    user = db.get_user_by_username(username)
    paid_amount = user.get('paid_amount', 0) if user else 0
    tickets_sold = len(my_tickets)
    total_value = tickets_sold * 25000
    amount_to_pay = total_value - paid_amount

    return render_template('agent_dashboard.html', tickets=my_tickets, amount_to_pay=amount_to_pay, tickets_sold=tickets_sold)


@app.route('/admin/delete/<ticket_id>')
def delete_ticket(ticket_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    ticket = db.get_ticket_by_id(ticket_id)
    if ticket:
        qr_image = ticket['qr_image']
        qr_path = os.path.join(QR_DIR, qr_image)
        if os.path.exists(qr_path):
            os.remove(qr_path)

    db.delete_ticket(ticket_id)
    flash(f'Ticket {ticket_id} deleted')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit/<ticket_id>', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_name = request.form['student_name']
        class_name = request.form['class_name']

        db.update_ticket(ticket_id, {
            'student_name': student_name,
            'class_name': class_name,
        })
        flash(f'Ticket {ticket_id} updated')
        return redirect(url_for('admin_dashboard'))

    ticket = db.get_ticket_by_id(ticket_id)
    if not ticket:
        flash('Ticket not found')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_ticket.html', ticket=ticket)


@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        role = request.form['role'].strip()

        existing = db.get_user_by_username(username)
        if existing:
            flash(f'Username "{username}" already exists!')
            return redirect(url_for('manage_users'))

        new_token = generate_unique_token()
        db.create_user(username, new_token, role)
        flash(f'User "{username}" created successfully! Token: {new_token}')
        return redirect(url_for('manage_users'))

    users = db.get_all_users()
    all_tickets = db.get_all_tickets()

    users_data = []
    for user in users:
        u_dict = dict(user)
        if u_dict['role'] == 'agent':
            t_sold = len([t for t in all_tickets if t['agent_username'] == u_dict['username']])
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

    user = db.get_user_by_username(username)
    if not user:
        flash('User not found')
        return redirect(url_for('manage_users'))

    action = request.form.get('action')

    if action == 'clear':
        t_sold = len(db.get_tickets_by_agent(username))
        db.update_user_paid_amount(username, t_sold * 25000)
        flash(f'Payment cleared for {username}')

    elif action == 'edit':
        try:
            new_paid = int(request.form.get('paid_amount', 0))
            db.update_user_paid_amount(username, new_paid)
            flash(f'Payment updated for {username}')
        except ValueError:
            flash('Invalid amount entered')

    return redirect(url_for('manage_users'))


if __name__ == '__main__':
    from waitress import serve
    print("Starting production server with Waitress on http://0.0.0.0:5000...")
    serve(app, host='0.0.0.0', port=5000, threads=10)
