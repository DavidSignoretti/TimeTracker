from app import db
from datetime import datetime, timedelta
from enum import Enum

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    
class QuoteStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    ACCEPTED = "accepted"
    INVOICED = "invoiced"
    REJECTED = "rejected"

class HourlyRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Name/description of the rate
    rate = db.Column(db.Float, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<HourlyRate {self.name}: ${self.rate} for client {self.client_id}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    province = db.Column(db.String(50), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    hourly_rate = db.Column(db.Float, nullable=False, default=0.0)  # Kept for backward compatibility
    time_entries = db.relationship('TimeEntry', backref='client', lazy=True, cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', backref='client', lazy=True, cascade="all, delete-orphan")
    hourly_rates = db.relationship('HourlyRate', backref='client', lazy=True, cascade="all, delete-orphan")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Client {self.name}>'

    def get_default_rate(self):
        # First try to get a rate marked as default
        default_rate = HourlyRate.query.filter_by(client_id=self.id, is_default=True).first()
        if default_rate:
            return default_rate.rate

        # If no default rate is set, use the legacy hourly_rate field
        return self.hourly_rate


class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    item = db.Column(db.String(100), nullable=False)  # Task or service provided
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)  # Link to a task if applicable
    date = db.Column(db.Date, nullable=False)
    time_in = db.Column(db.Time, nullable=False)
    time_out = db.Column(db.Time, nullable=False)
    total_hours = db.Column(db.Float, nullable=False)  # Stored for quick access
    hourly_rate = db.Column(db.Float, nullable=False)  # Store the rate at the time of entry
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=True)  # Link to a quote if applicable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TimeEntry {self.id}: {self.item} for {self.client_id} on {self.date}>'


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), nullable=False, unique=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date_issued = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    date_due = db.Column(db.Date, nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    hst_rate = db.Column(db.Float, nullable=False, default=0.13)  # 13% is typical HST rate
    hst_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, sent, paid
    notes = db.Column(db.Text, nullable=True)
    time_entries = db.relationship('TimeEntry', backref='invoice', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Invoice {self.invoice_number} for {self.client_id}>'


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=TaskStatus.TODO.value)
    priority = db.Column(db.Integer, nullable=False, default=0)  # 0=low, 1=medium, 2=high
    due_date = db.Column(db.Date, nullable=True)
    estimated_hours = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add relationships
    client = db.relationship('Client', backref=db.backref('tasks', lazy=True, cascade="all, delete-orphan"))
    time_entries = db.relationship('TimeEntry', backref='task', lazy=True)

    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(20), nullable=False, unique=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date_issued = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    date_valid_until = db.Column(db.Date, nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    hst_rate = db.Column(db.Float, nullable=False, default=0.13)  # 13% is typical HST rate
    hst_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default=QuoteStatus.PENDING.value)
    notes = db.Column(db.Text, nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)  # Link to invoice if converted
    time_entries = db.relationship('TimeEntry', backref='quote', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add relationship to client
    client = db.relationship('Client', backref=db.backref('quotes', lazy=True, cascade="all, delete-orphan"))
    # Add relationship to invoice if converted
    invoice = db.relationship('Invoice', backref=db.backref('quote', uselist=False), lazy=True)

    def __repr__(self):
        return f'<Quote {self.quote_number} for {self.client_id}>'
    
    def convert_to_invoice(self):
        """Convert this quote to an invoice"""
        from app import db
        
        # Create a new invoice based on this quote
        invoice = Invoice(
            invoice_number=self.quote_number.replace('QUO-', 'INV-'),
            client_id=self.client_id,
            date_issued=datetime.utcnow().date(),
            date_due=datetime.utcnow().date() + timedelta(days=30),
            subtotal=self.subtotal,
            hst_rate=self.hst_rate,
            hst_amount=self.hst_amount,
            total=self.total,
            status='draft',
            notes=self.notes
        )
        
        db.session.add(invoice)
        db.session.flush()  # Get the invoice ID
        
        # Link the quote to the invoice
        self.invoice_id = invoice.id
        self.status = QuoteStatus.INVOICED.value
        
        # Link the time entries to the invoice
        for entry in self.time_entries:
            entry.invoice_id = invoice.id
            
        db.session.commit()
        return invoice


class CompanySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    province = db.Column(db.String(50), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(100), nullable=True)
    tax_number = db.Column(db.String(50), nullable=True)  # For HST/GST number
    default_hst_rate = db.Column(db.Float, nullable=False, default=0.13)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CompanySettings {self.company_name}>'

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    is_billable = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = db.relationship('Client', backref=db.backref('calendar_events', lazy=True, cascade="all, delete-orphan"))
    task = db.relationship('Task', backref=db.backref('calendar_events', lazy=True))

    def __repr__(self):
        return f'<CalendarEvent {self.id}: {self.title}>'
