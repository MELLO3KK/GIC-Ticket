import os
import uuid
import random
import qrcode
import io
import csv
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, Response
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
    user = db.get_user_by_username(username)
    can_sell = user.get('can_sell_tickets', True) if user else True

    if request.method == 'POST':
        if not can_sell:
            flash('Ticketing has been suspended by the Admin.')
            return redirect(url_for('agent_dashboard'))
            
        student_name = request.form['student_name']
        class_name = request.form['class_name']

        # Make ticket ID and secure token
        ticket_id = str(uuid.uuid4())[:8]
        qr_token = str(uuid.uuid4())
        qr_filename = f"{ticket_id}.png"

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
    paid_amount = user.get('paid_amount', 0) if user else 0
    tickets_sold = len(my_tickets)
    total_value = tickets_sold * 25000
    amount_to_pay = total_value - paid_amount

    return render_template('agent_dashboard.html', tickets=my_tickets, amount_to_pay=amount_to_pay, tickets_sold=tickets_sold, can_sell=can_sell)


@app.route('/admin/delete/<ticket_id>')
def delete_ticket(ticket_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    ticket = db.get_ticket_by_id(ticket_id)

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


@app.route('/qr/<qr_token>')
def serve_qr(qr_token):
    if not qr_token:
        return "Invalid QR token", 400
        
    img = qrcode.make(qr_token)
    template_path = os.path.join(BASE_DIR, 'template.jpg')
    
    if os.path.exists(template_path):
        qr_img = img.convert("RGBA")
        design = Image.open(template_path).convert("RGBA")
        
        target_size = (325, 325)
        target_position = (150, 375)
        
        qr_resized = qr_img.resize(target_size, Image.Resampling.LANCZOS)
        design.paste(qr_resized, target_position, qr_resized)
        
        design = design.convert("RGB")
        img_io = io.BytesIO()
        design.save(img_io, 'JPEG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name=f"ticket_{qr_token}.jpg")
    else:
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f"qr_{qr_token}.png")


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
    return render_template('admin_users.html', users=users)


@app.route('/admin/payment/<username>', methods=['POST'])
def update_payment(username):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    user = db.get_user_by_username(username)
    if not user:
        flash('User not found')
        return redirect(url_for('manage_agents'))

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

    return redirect(url_for('manage_agents'))

@app.route('/admin/agents', methods=['GET'])
def manage_agents():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    users = db.get_all_users()
    all_tickets = db.get_all_tickets()

    agents_data = []
    for user in users:
        u_dict = dict(user)
        if u_dict['role'] == 'agent':
            t_sold = len([t for t in all_tickets if t['agent_username'] == u_dict['username']])
            u_dict['tickets_sold'] = t_sold
            u_dict['total_value'] = t_sold * 25000
            u_dict['paid_amount'] = u_dict.get('paid_amount', 0)
            u_dict['amount_to_pay'] = u_dict['total_value'] - u_dict['paid_amount']
            u_dict['can_sell_tickets'] = u_dict.get('can_sell_tickets', True)
            agents_data.append(u_dict)

    return render_template('admin_agents.html', agents=agents_data)

@app.route('/admin/agents/toggle/<username>', methods=['POST'])
def toggle_agent(username):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    user = db.get_user_by_username(username)
    if user and user['role'] == 'agent':
        new_status = not user.get('can_sell_tickets', True)
        db.update_user_can_sell(username, new_status)
        flash(f"Agent '{username}' selling status updated to {new_status}")
    
    return redirect(url_for('manage_agents'))

@app.route('/admin/agents/toggle_all/<status>', methods=['POST'])
def toggle_all_agents(status):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    can_sell = (status == 'allow')
    db.update_all_agents_can_sell(can_sell)
    flash(f"All agents selling statuses set to {can_sell}")
    return redirect(url_for('manage_agents'))

@app.route('/admin/export_csv')
def admin_export_csv():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    tickets = db.get_all_tickets()
    
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow(('Ticket ID', 'Student Name', 'Class / Grade', 'Sold By', 'QR Token'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for ticket in tickets:
            writer.writerow((
                ticket.get('id', ''),
                ticket.get('student_name', ''),
                ticket.get('class_name', ''),
                ticket.get('agent_username', ''),
                ticket.get('qr_token', '')
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="all_tickets.csv")
    return response

@app.route('/agent/export_csv')
def agent_export_csv():
    if session.get('role') != 'agent':
        return redirect(url_for('login'))

    username = session['username']
    tickets = db.get_tickets_by_agent(username)
    
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow(('Ticket ID', 'Student Name', 'Class / Grade', 'QR Token'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for ticket in tickets:
            writer.writerow((
                ticket.get('id', ''),
                ticket.get('student_name', ''),
                ticket.get('class_name', ''),
                ticket.get('qr_token', '')
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename=f"my_tickets_{username}.csv")
    return response


@app.route('/admin/check-in', methods=['GET', 'POST'])
def admin_check_in():
    if session.get('role') != 'admin':
        if request.method == 'POST':
            return {"success": False, "message": "Unauthorized"}, 403
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json() or {}
        qr_token = data.get('qr_token')

        if not qr_token:
            return {"success": False, "message": "No QR token provided"}, 400

        ticket = db.get_ticket_by_qr(qr_token)
        if not ticket:
            return {"success": False, "message": "Invalid QR code — ticket not found"}, 404

        # Duplicate check-in prevention
        last = db.get_last_attendance(ticket['id'])
        if last and last['event_type'] == 'Check-in':
            return {
                "success": False,
                "message": f"{ticket['student_name']} is already checked in",
                "student_name": ticket['student_name'],
                "class_name": ticket.get('class_name', ''),
            }, 409

        try:
            ts = db.log_attendance(ticket['id'], ticket['student_name'], "Check-in")
            return {
                "success": True,
                "message": f"Check-in successful",
                "student_name": ticket['student_name'],
                "class_name": ticket.get('class_name', ''),
                "timestamp": ts,
            }
        except Exception as e:
            return {"success": False, "message": "Server error: " + str(e)}, 500

    return render_template('check_in.html')


@app.route('/admin/check-out', methods=['GET', 'POST'])
def admin_check_out():
    if session.get('role') != 'admin':
        if request.method == 'POST':
            return {"success": False, "message": "Unauthorized"}, 403
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json() or {}
        qr_token = data.get('qr_token')
        
        if not qr_token:
            return {"success": False, "message": "No QR token provided"}, 400
            
        ticket = db.get_ticket_by_qr(qr_token)
        if not ticket:
            return {"success": False, "message": "Invalid QR token"}, 404
            
        try:
            ts = db.log_attendance(ticket['id'], ticket['student_name'], "Check-out")
            return {
                "success": True,
                "message": f"Check-out successful",
                "student_name": ticket['student_name'],
                "class_name": ticket.get('class_name', ''),
                "timestamp": ts,
            }
        except Exception as e:
            return {"success": False, "message": "Error logging attendance: " + str(e)}, 500

    return render_template('check_out.html')


@app.route('/admin/attendance')
def admin_attendance():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    logs = db.get_all_attendance()
    return render_template('admin_attendance.html', logs=logs)


@app.route('/admin/attendance/export_csv')
def admin_export_attendance_csv():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    logs = db.get_all_attendance()
    
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow(('Ticket ID', 'Student Name', 'Event Type', 'Timestamp'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for log in logs:
            writer.writerow((
                log.get('ticket_id', ''),
                log.get('student_name', ''),
                log.get('event_type', ''),
                log.get('timestamp', '')
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="attendance_logs.csv")
    return response


if __name__ == '__main__':
    from waitress import serve
    print("Starting production server with Waitress on http://0.0.0.0:5000...")
    serve(app, host='0.0.0.0', port=5000, threads=10)
