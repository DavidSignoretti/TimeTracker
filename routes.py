from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from sqlalchemy import func, desc
from app import app, db
from models import Client, TimeEntry, Invoice, CompanySettings, Task, TaskStatus
from utils import generate_invoice_pdf, calculate_hours
from datetime import datetime, date, timedelta
import os
import io

# Add utility function for template context
@app.context_processor
def utility_processor():
    def current_year():
        return datetime.now().year
    return dict(current_year=current_year)
    
# Task routes
@app.route('/tasks')
def tasks():
    # Get filter parameters
    client_id = request.args.get('client_id', type=int)
    status = request.args.get('status')
    priority = request.args.get('priority', type=int)
    
    # Base query
    query = Task.query
    
    # Apply filters
    if client_id:
        query = query.filter_by(client_id=client_id)
    if status:
        query = query.filter_by(status=status)
    if priority is not None:  # Check for None since priority can be 0 (low)
        query = query.filter_by(priority=priority)
    
    # Order by priority (high to low) and due date (oldest first)
    tasks = query.order_by(Task.priority.desc(), Task.due_date).all()
    clients = Client.query.order_by(Client.name).all()
    
    return render_template('tasks.html', 
                          tasks=tasks,
                          clients=clients,
                          selected_client_id=client_id,
                          status=status,
                          priority=priority)

@app.route('/tasks/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        # Extract data from form
        title = request.form.get('title')
        client_id = request.form.get('client_id')
        description = request.form.get('description')
        status = request.form.get('status')
        priority = int(request.form.get('priority'))
        due_date_str = request.form.get('due_date')
        estimated_hours = request.form.get('estimated_hours')
        
        # Parse due date if provided
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        
        # Parse estimated hours if provided
        est_hours = None
        if estimated_hours:
            est_hours = float(estimated_hours)
        
        # Create new task
        new_task = Task(
            title=title,
            client_id=int(client_id),
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            estimated_hours=est_hours
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash('Task added successfully!', 'success')
        return redirect(url_for('tasks'))
    
    # GET request - show the form
    clients = Client.query.order_by(Client.name).all()
    return render_template('add_task.html', clients=clients)

@app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        # Extract data from form
        task.title = request.form.get('title')
        task.client_id = int(request.form.get('client_id'))
        task.description = request.form.get('description')
        task.status = request.form.get('status')
        task.priority = int(request.form.get('priority'))
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        else:
            task.due_date = None
        
        estimated_hours = request.form.get('estimated_hours')
        if estimated_hours:
            task.estimated_hours = float(estimated_hours)
        else:
            task.estimated_hours = None
        
        db.session.commit()
        
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks'))
    
    # GET request - show the form with task data
    clients = Client.query.order_by(Client.name).all()
    return render_template('edit_task.html', task=task, clients=clients)

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks'))

@app.route('/timer/task/<int:task_id>')
def timer_with_task(task_id):
    task = Task.query.get_or_404(task_id)
    clients = Client.query.all()
    
    # Pre-fill the timer form with task information
    return render_template('timer.html', 
                          clients=clients,
                          selected_client_id=task.client_id,
                          item=task.title,
                          task_id=task.id)

# Home route
@app.route('/')
def index():
    # Get some stats for the dashboard
    total_clients = Client.query.count()
    total_unbilled_hours = db.session.query(func.sum(TimeEntry.total_hours)).filter(TimeEntry.invoice_id.is_(None)).scalar() or 0
    total_unbilled_amount = db.session.query(
        func.sum(TimeEntry.total_hours * TimeEntry.hourly_rate)
    ).filter(TimeEntry.invoice_id.is_(None)).scalar() or 0
    
    recent_time_entries = TimeEntry.query.order_by(TimeEntry.date.desc()).limit(5).all()
    recent_invoices = Invoice.query.order_by(Invoice.date_issued.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_clients=total_clients,
                         total_unbilled_hours=total_unbilled_hours,
                         total_unbilled_amount=total_unbilled_amount,
                         recent_time_entries=recent_time_entries,
                         recent_invoices=recent_invoices)

# Client routes
@app.route('/clients')
def clients():
    clients = Client.query.order_by(Client.name).all()
    return render_template('clients.html', clients=clients)

@app.route('/clients/add', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        try:
            name = request.form['name']
            address = request.form['address']
            city = request.form['city']
            province = request.form['province']
            postal_code = request.form['postal_code']
            phone = request.form['phone']
            email = request.form['email']
            contact_person = request.form['contact_person']
            hourly_rate = float(request.form['hourly_rate'])
            
            new_client = Client(
                name=name,
                address=address,
                city=city,
                province=province,
                postal_code=postal_code,
                phone=phone,
                email=email,
                contact_person=contact_person,
                hourly_rate=hourly_rate
            )
            
            db.session.add(new_client)
            db.session.commit()
            
            flash('Client added successfully!', 'success')
            return redirect(url_for('clients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding client: {str(e)}', 'danger')
    
    return render_template('add_client.html')

@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        try:
            client.name = request.form['name']
            client.address = request.form['address']
            client.city = request.form['city']
            client.province = request.form['province']
            client.postal_code = request.form['postal_code']
            client.phone = request.form['phone']
            client.email = request.form['email']
            client.contact_person = request.form['contact_person']
            client.hourly_rate = float(request.form['hourly_rate'])
            
            db.session.commit()
            
            flash('Client updated successfully!', 'success')
            return redirect(url_for('clients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating client: {str(e)}', 'danger')
    
    return render_template('edit_client.html', client=client)

@app.route('/clients/<int:client_id>/delete', methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    try:
        db.session.delete(client)
        db.session.commit()
        flash('Client deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting client: {str(e)}', 'danger')
    
    return redirect(url_for('clients'))

# Time Entry routes
@app.route('/time-entries')
def time_entries():
    entries = TimeEntry.query.order_by(TimeEntry.date.desc(), TimeEntry.time_in.desc()).all()
    clients = Client.query.order_by(Client.name).all()
    return render_template('time_entries.html', entries=entries, clients=clients)

@app.route('/timer')
def timer():
    clients = Client.query.order_by(Client.name).all()
    today = date.today()
    return render_template('timer.html', clients=clients, today=today)

@app.route('/save-timer', methods=['POST'])
def save_timer():
    try:
        client_id = int(request.form['client_id'])
        client = Client.query.get_or_404(client_id)
        
        item = request.form['item']
        location = request.form['location']
        entry_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        time_in = datetime.strptime(request.form['time_in'], '%H:%M').time()
        time_out = datetime.strptime(request.form['time_out'], '%H:%M').time()
        total_hours = float(request.form['total_hours'])
        
        new_entry = TimeEntry(
            client_id=client_id,
            location=location,
            item=item,
            date=entry_date,
            time_in=time_in,
            time_out=time_out,
            total_hours=total_hours,
            hourly_rate=client.hourly_rate
        )
        
        db.session.add(new_entry)
        db.session.commit()
        
        flash('Time entry saved successfully!', 'success')
        return redirect(url_for('time_entries'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving time entry: {str(e)}', 'danger')
        return redirect(url_for('timer'))

@app.route('/time-entries/add', methods=['GET', 'POST'])
def add_time_entry():
    clients = Client.query.order_by(Client.name).all()
    
    if request.method == 'POST':
        try:
            client_id = int(request.form['client_id'])
            client = Client.query.get_or_404(client_id)
            
            location = request.form['location']
            item = request.form['item']
            date_str = request.form['date']
            time_in_str = request.form['time_in']
            time_out_str = request.form['time_out']
            
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_in = datetime.strptime(time_in_str, '%H:%M').time()
            time_out = datetime.strptime(time_out_str, '%H:%M').time()
            
            # Calculate total hours
            total_hours = calculate_hours(time_in, time_out)
            
            new_entry = TimeEntry(
                client_id=client_id,
                location=location,
                item=item,
                date=entry_date,
                time_in=time_in,
                time_out=time_out,
                total_hours=total_hours,
                hourly_rate=client.hourly_rate
            )
            
            db.session.add(new_entry)
            db.session.commit()
            
            flash('Time entry added successfully!', 'success')
            return redirect(url_for('time_entries'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding time entry: {str(e)}', 'danger')
    
    return render_template('add_time_entry.html', clients=clients, today=date.today())

@app.route('/time-entries/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_time_entry(entry_id):
    entry = TimeEntry.query.get_or_404(entry_id)
    clients = Client.query.order_by(Client.name).all()
    
    if request.method == 'POST':
        try:
            client_id = int(request.form['client_id'])
            client = Client.query.get_or_404(client_id)
            
            entry.client_id = client_id
            entry.location = request.form['location']
            entry.item = request.form['item']
            entry.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            entry.time_in = datetime.strptime(request.form['time_in'], '%H:%M').time()
            entry.time_out = datetime.strptime(request.form['time_out'], '%H:%M').time()
            
            # Recalculate total hours
            entry.total_hours = calculate_hours(entry.time_in, entry.time_out)
            entry.hourly_rate = client.hourly_rate
            
            db.session.commit()
            
            flash('Time entry updated successfully!', 'success')
            return redirect(url_for('time_entries'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating time entry: {str(e)}', 'danger')
    
    return render_template('edit_time_entry.html', entry=entry, clients=clients)

@app.route('/time-entries/<int:entry_id>/delete', methods=['POST'])
def delete_time_entry(entry_id):
    entry = TimeEntry.query.get_or_404(entry_id)
    
    try:
        db.session.delete(entry)
        db.session.commit()
        flash('Time entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting time entry: {str(e)}', 'danger')
    
    return redirect(url_for('time_entries'))

# Invoice routes
@app.route('/invoices')
def invoices():
    invoices = Invoice.query.order_by(Invoice.date_issued.desc()).all()
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoices/create', methods=['GET', 'POST'])
def create_invoice():
    clients = Client.query.order_by(Client.name).all()
    
    if request.method == 'POST':
        try:
            client_id = int(request.form['client_id'])
            client = Client.query.get_or_404(client_id)
            
            # Find the next invoice number
            last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
            if last_invoice:
                # Extract the numeric part and increment
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                invoice_number = f"INV-{last_num + 1:04d}"
            else:
                invoice_number = "INV-0001"
            
            date_issued = datetime.strptime(request.form['date_issued'], '%Y-%m-%d').date()
            
            # Calculate due date (30 days from issue)
            date_due = date_issued + timedelta(days=30)
            
            # Get the selected time entries
            selected_entries = request.form.getlist('time_entries')
            if not selected_entries:
                flash('Please select at least one time entry for the invoice', 'danger')
                return redirect(url_for('create_invoice'))
            
            # Calculate the subtotal and total
            entries = TimeEntry.query.filter(TimeEntry.id.in_(selected_entries)).all()
            subtotal = sum(entry.total_hours * entry.hourly_rate for entry in entries)
            
            # Get company settings for HST rate
            company = CompanySettings.query.first()
            hst_rate = company.default_hst_rate if company else 0.13  # Default to 13% if not set
            
            hst_amount = subtotal * hst_rate
            total = subtotal + hst_amount
            
            new_invoice = Invoice(
                invoice_number=invoice_number,
                client_id=client_id,
                date_issued=date_issued,
                date_due=date_due,
                subtotal=subtotal,
                hst_rate=hst_rate,
                hst_amount=hst_amount,
                total=total,
                status='draft',
                notes=request.form.get('notes', '')
            )
            
            db.session.add(new_invoice)
            db.session.commit()
            
            # Update the time entries to link them to this invoice
            for entry in entries:
                entry.invoice_id = new_invoice.id
            
            db.session.commit()
            
            flash('Invoice created successfully!', 'success')
            return redirect(url_for('view_invoice', invoice_id=new_invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating invoice: {str(e)}', 'danger')
            return redirect(url_for('create_invoice'))
    
    return render_template('create_invoice.html', clients=clients)

@app.route('/get_unbilled_entries/<int:client_id>')
def get_unbilled_entries(client_id):
    entries = TimeEntry.query.filter_by(client_id=client_id, invoice_id=None).order_by(TimeEntry.date).all()
    
    entries_data = []
    for entry in entries:
        amount = entry.total_hours * entry.hourly_rate
        entries_data.append({
            'id': entry.id,
            'date': entry.date.strftime('%Y-%m-%d'),
            'item': entry.item,
            'location': entry.location or '',
            'hours': f"{entry.total_hours:.2f}",
            'rate': f"${entry.hourly_rate:.2f}",
            'amount': f"${amount:.2f}"
        })
    
    return jsonify(entries_data)

@app.route('/invoices/<int:invoice_id>')
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    company = CompanySettings.query.first()
    
    return render_template('view_invoice.html', invoice=invoice, company=company)

@app.route('/invoices/<int:invoice_id>/update_status', methods=['POST'])
def update_invoice_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    try:
        status = request.form['status']
        invoice.status = status
        db.session.commit()
        flash(f'Invoice status updated to {status}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating invoice status: {str(e)}', 'danger')
    
    return redirect(url_for('view_invoice', invoice_id=invoice_id))

@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    try:
        # First, unlink all time entries
        for entry in invoice.time_entries:
            entry.invoice_id = None
        
        db.session.delete(invoice)
        db.session.commit()
        flash('Invoice deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {str(e)}', 'danger')
    
    return redirect(url_for('invoices'))

@app.route('/invoices/<int:invoice_id>/download')
def download_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    company = CompanySettings.query.first()
    
    if not company:
        flash('Please set up your company information first', 'danger')
        return redirect(url_for('company_settings'))
    
    try:
        pdf_data = generate_invoice_pdf(invoice, company)
        
        # Create a BytesIO object
        pdf_io = io.BytesIO(pdf_data)
        pdf_io.seek(0)
        
        return send_file(
            pdf_io,
            as_attachment=True,
            download_name=f"Invoice_{invoice.invoice_number}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('view_invoice', invoice_id=invoice_id))

# Reports route
@app.route('/reports')
def reports():
    clients = Client.query.order_by(Client.name).all()
    
    # Default to current month
    today = date.today()
    start_date = date(today.year, today.month, 1)
    end_date = (date(today.year, today.month + 1, 1) - timedelta(days=1)) if today.month < 12 else date(today.year, 12, 31)
    
    # Get query parameters
    client_id = request.args.get('client_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Build the query
    query = TimeEntry.query.filter(TimeEntry.date.between(start_date, end_date))
    
    if client_id:
        query = query.filter_by(client_id=client_id)
    
    entries = query.order_by(TimeEntry.date).all()
    
    # Calculate totals
    total_hours = sum(entry.total_hours for entry in entries)
    total_amount = sum(entry.total_hours * entry.hourly_rate for entry in entries)
    
    # Group by client
    client_summary = {}
    for entry in entries:
        if entry.client_id not in client_summary:
            client_summary[entry.client_id] = {
                'name': entry.client.name,
                'hours': 0,
                'amount': 0
            }
        
        client_summary[entry.client_id]['hours'] += entry.total_hours
        client_summary[entry.client_id]['amount'] += entry.total_hours * entry.hourly_rate
    
    return render_template('reports.html', 
                        clients=clients,
                        entries=entries,
                        total_hours=total_hours,
                        total_amount=total_amount,
                        client_summary=client_summary,
                        start_date=start_date,
                        end_date=end_date,
                        selected_client_id=client_id)

# Company Settings routes
@app.route('/company-settings', methods=['GET', 'POST'])
def company_settings():
    company = CompanySettings.query.first()
    
    if not company:
        company = CompanySettings(
            company_name="Your Company Name",
            default_hst_rate=0.13
        )
        db.session.add(company)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            company.company_name = request.form['company_name']
            company.address = request.form['address']
            company.city = request.form['city']
            company.province = request.form['province']
            company.postal_code = request.form['postal_code']
            company.phone = request.form['phone']
            company.email = request.form['email']
            company.website = request.form['website']
            company.tax_number = request.form['tax_number']
            company.default_hst_rate = float(request.form['default_hst_rate'])
            
            db.session.commit()
            
            flash('Company settings updated successfully!', 'success')
            return redirect(url_for('company_settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating company settings: {str(e)}', 'danger')
    
    return render_template('company_settings.html', company=company)
