# app.py — Main Flask Application for Cafe Management System
# This file registers all the routes (URLs) and ties together
# the database, models, and HTML templates.

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db
from models import Customer, Employee, MenuItem, Order, OrderItem, Reservation, Payment
from datetime import datetime

# ── App Setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Secret key for flash messages (change this in production!)
app.config['SECRET_KEY'] = 'cafe-secret-key-2024'

# SQLite database stored in the project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Bind the db instance to this Flask app
db.init_app(app)


# ── Context Processor ─────────────────────────────────────────────────────────
# Makes stats available in every template (used by sidebar)
@app.context_processor
def inject_stats():
    return {
        'total_orders': Order.query.count(),
        'total_customers': Customer.query.count(),
        'total_staff': Employee.query.count(),
        'pending_orders': Order.query.filter_by(status='Pending').count(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    """Admin dashboard — shows key stats and recent orders."""
    stats = {
        'total_orders': Order.query.count(),
        'total_customers': Customer.query.count(),
        'total_menu_items': MenuItem.query.count(),
        'total_revenue': db.session.query(db.func.sum(Payment.amount)).scalar() or 0,
        'pending_orders': Order.query.filter_by(status='Pending').count(),
        'total_staff': Employee.query.count(),
        'todays_reservations': Reservation.query.filter(
            db.func.date(Reservation.date) == datetime.utcnow().date()
        ).count(),
    }
    # 5 most recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    return render_template('dashboard.html', stats=stats, recent_orders=recent_orders)


# ══════════════════════════════════════════════════════════════════════════════
# MENU MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/menu')
def menu():
    """List all menu items, grouped by category."""
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.item_name).all()
    categories = db.session.query(MenuItem.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('menu.html', items=items, categories=categories)


@app.route('/menu/add', methods=['POST'])
def add_menu_item():
    """Add a new menu item from the form."""
    item = MenuItem(
        item_name=request.form['item_name'],
        price=float(request.form['price']),
        category=request.form['category'],
        description=request.form.get('description', '')
    )
    db.session.add(item)
    db.session.commit()
    flash('Menu item added successfully!', 'success')
    return redirect(url_for('menu'))


@app.route('/menu/edit/<int:item_id>', methods=['POST'])
def edit_menu_item(item_id):
    """Edit an existing menu item."""
    item = MenuItem.query.get_or_404(item_id)
    item.item_name = request.form['item_name']
    item.price = float(request.form['price'])
    item.category = request.form['category']
    item.description = request.form.get('description', '')
    item.available = 'available' in request.form
    db.session.commit()
    flash('Menu item updated!', 'success')
    return redirect(url_for('menu'))


@app.route('/menu/delete/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    """Delete a menu item."""
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Menu item deleted.', 'info')
    return redirect(url_for('menu'))


# ══════════════════════════════════════════════════════════════════════════════
# ORDERS MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/orders')
def orders():
    """List all orders with filters."""
    status_filter = request.args.get('status', '')
    query = Order.query.order_by(Order.order_date.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_orders = query.all()
    customers = Customer.query.all()
    employees = Employee.query.all()
    menu_items = MenuItem.query.filter_by(available=True).all()
    return render_template('orders.html',
                           orders=all_orders,
                           customers=customers,
                           employees=employees,
                           menu_items=menu_items,
                           status_filter=status_filter)


@app.route('/orders/create', methods=['POST'])
def create_order():
    """Create a new order for a customer."""
    # Auto-create customer if new name given
    customer_id = request.form.get('customer_id')
    if not customer_id:
        customer = Customer(
            name=request.form['customer_name'],
            contact=request.form.get('customer_contact', 'N/A')
        )
        db.session.add(customer)
        db.session.flush()   # get the id before commit
        customer_id = customer.id

    order = Order(
        customer_id=customer_id,
        employee_id=request.form.get('employee_id') or None,
        status='Pending'
    )
    db.session.add(order)
    db.session.commit()
    flash(f'Order #{order.id} created!', 'success')
    return redirect(url_for('order_detail', order_id=order.id))


@app.route('/orders/<int:order_id>')
def order_detail(order_id):
    """View a single order and manage its items."""
    order = Order.query.get_or_404(order_id)
    menu_items = MenuItem.query.filter_by(available=True).all()
    return render_template('order_detail.html', order=order, menu_items=menu_items)


@app.route('/orders/<int:order_id>/add_item', methods=['POST'])
def add_order_item(order_id):
    """Add a menu item to an existing order."""
    order = Order.query.get_or_404(order_id)
    menu_item_id = int(request.form['menu_item_id'])
    quantity = int(request.form.get('quantity', 1))

    menu_item = MenuItem.query.get_or_404(menu_item_id)

    # Check if item already in order — increase qty instead
    existing = OrderItem.query.filter_by(order_id=order_id, menu_item_id=menu_item_id).first()
    if existing:
        existing.quantity += quantity
        existing.subtotal = existing.quantity * menu_item.price
    else:
        item = OrderItem(
            order_id=order_id,
            menu_item_id=menu_item_id,
            quantity=quantity,
            subtotal=quantity * menu_item.price
        )
        db.session.add(item)

    # Recalculate order total
    db.session.flush()
    order.total_amount = sum(i.subtotal for i in order.items)
    db.session.commit()
    flash('Item added to order!', 'success')
    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/orders/<int:order_id>/remove_item/<int:item_id>', methods=['POST'])
def remove_order_item(order_id, item_id):
    """Remove a line item from an order."""
    item = OrderItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.flush()
    order = Order.query.get(order_id)
    order.total_amount = sum(i.subtotal for i in order.items)
    db.session.commit()
    flash('Item removed.', 'info')
    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/orders/<int:order_id>/update_status', methods=['POST'])
def update_order_status(order_id):
    """Update the status of an order."""
    order = Order.query.get_or_404(order_id)
    order.status = request.form['status']
    db.session.commit()
    flash(f'Order status updated to {order.status}!', 'success')
    return redirect(url_for('order_detail', order_id=order_id))


# ══════════════════════════════════════════════════════════════════════════════
# STAFF MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/staff')
def staff():
    """List all employees/staff."""
    employees = Employee.query.order_by(Employee.name).all()
    return render_template('staff.html', employees=employees)


@app.route('/staff/add', methods=['POST'])
def add_staff():
    """Add a new staff member."""
    employee = Employee(
        name=request.form['name'],
        position=request.form['position'],
        contact=request.form['contact']
    )
    db.session.add(employee)
    db.session.commit()
    flash('Staff member added!', 'success')
    return redirect(url_for('staff'))


@app.route('/staff/edit/<int:emp_id>', methods=['POST'])
def edit_staff(emp_id):
    """Edit an existing staff member."""
    emp = Employee.query.get_or_404(emp_id)
    emp.name = request.form['name']
    emp.position = request.form['position']
    emp.contact = request.form['contact']
    db.session.commit()
    flash('Staff updated!', 'success')
    return redirect(url_for('staff'))


@app.route('/staff/delete/<int:emp_id>', methods=['POST'])
def delete_staff(emp_id):
    """Delete a staff member."""
    emp = Employee.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    flash('Staff member removed.', 'info')
    return redirect(url_for('staff'))


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/customers')
def customers():
    """List all customers."""
    all_customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers.html', customers=all_customers)


@app.route('/customers/add', methods=['POST'])
def add_customer():
    customer = Customer(
        name=request.form['name'],
        contact=request.form['contact']
    )
    db.session.add(customer)
    db.session.commit()
    flash('Customer added!', 'success')
    return redirect(url_for('customers'))


@app.route('/customers/delete/<int:cust_id>', methods=['POST'])
def delete_customer(cust_id):
    customer = Customer.query.get_or_404(cust_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer removed.', 'info')
    return redirect(url_for('customers'))


# ══════════════════════════════════════════════════════════════════════════════
# RESERVATIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/reservations')
def reservations():
    """List all table reservations."""
    all_reservations = Reservation.query.order_by(Reservation.date.desc()).all()
    customers = Customer.query.all()
    return render_template('reservations.html',
                           reservations=all_reservations,
                           customers=customers)


@app.route('/reservations/add', methods=['POST'])
def add_reservation():
    """Create a new table reservation."""
    date_str = request.form['date']
    date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')

    # Handle walk-in (no registered customer)
    customer_id = request.form.get('customer_id')
    if not customer_id:
        customer = Customer(
            name=request.form['guest_name'],
            contact=request.form.get('guest_contact', 'N/A')
        )
        db.session.add(customer)
        db.session.flush()
        customer_id = customer.id

    reservation = Reservation(
        customer_id=customer_id,
        date=date,
        guest_count=int(request.form['guest_count']),
        table_no=int(request.form['table_no'])
    )
    db.session.add(reservation)
    db.session.commit()
    flash('Reservation booked!', 'success')
    return redirect(url_for('reservations'))


@app.route('/reservations/cancel/<int:res_id>', methods=['POST'])
def cancel_reservation(res_id):
    """Cancel a reservation."""
    res = Reservation.query.get_or_404(res_id)
    res.status = 'Cancelled'
    db.session.commit()
    flash('Reservation cancelled.', 'info')
    return redirect(url_for('reservations'))


# ══════════════════════════════════════════════════════════════════════════════
# BILLING & PAYMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/billing')
def billing():
    """Show all unpaid orders for billing."""
    # Orders that are not yet paid
    unpaid_orders = (
        Order.query
        .filter(Order.status != 'Cancelled')
        .filter(~Order.id.in_(
            db.session.query(Payment.order_id)
        ))
        .order_by(Order.order_date.desc())
        .all()
    )
    paid_orders = Payment.query.order_by(Payment.paid_at.desc()).limit(10).all()
    return render_template('billing.html', unpaid_orders=unpaid_orders, paid_orders=paid_orders)


@app.route('/billing/pay/<int:order_id>', methods=['POST'])
def process_payment(order_id):
    """Process payment for a given order."""
    order = Order.query.get_or_404(order_id)
    payment = Payment(
        order_id=order_id,
        amount=order.total_amount,
        method=request.form['method']
    )
    order.status = 'Delivered'
    db.session.add(payment)
    db.session.commit()
    flash(f'Payment of ₹{order.total_amount:.2f} processed via {payment.method}!', 'success')
    return redirect(url_for('billing'))


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP — Create tables and seed sample data
# ══════════════════════════════════════════════════════════════════════════════

def seed_data():
    """Add sample data if the database is empty."""
    if MenuItem.query.count() == 0:
        # Sample menu items
        items = [
            MenuItem(item_name='Espresso', price=80, category='Drinks', description='Strong Italian coffee'),
            MenuItem(item_name='Cappuccino', price=120, category='Drinks', description='Espresso with steamed milk foam'),
            MenuItem(item_name='Latte', price=140, category='Drinks', description='Smooth espresso with milk'),
            MenuItem(item_name='Cold Coffee', price=160, category='Drinks', description='Chilled blended coffee'),
            MenuItem(item_name='Masala Chai', price=50, category='Drinks', description='Spiced Indian tea'),
            MenuItem(item_name='Sandwich', price=120, category='Food', description='Grilled veggie sandwich'),
            MenuItem(item_name='Burger', price=180, category='Food', description='Classic beef burger'),
            MenuItem(item_name='Pasta', price=220, category='Food', description='Creamy penne pasta'),
            MenuItem(item_name='Cheesecake', price=150, category='Desserts', description='New York style cheesecake'),
            MenuItem(item_name='Brownie', price=100, category='Desserts', description='Warm chocolate brownie'),
        ]
        db.session.add_all(items)

    if Employee.query.count() == 0:
        staff = [
            Employee(name='Ravi Kumar', position='Manager', contact='9876543210'),
            Employee(name='Priya Singh', position='Waiter', contact='9876543211'),
            Employee(name='Arjun Patel', position='Chef', contact='9876543212'),
            Employee(name='Sneha Rao', position='Cashier', contact='9876543213'),
        ]
        db.session.add_all(staff)

    if Customer.query.count() == 0:
        custs = [
            Customer(name='Amit Sharma', contact='9000000001'),
            Customer(name='Neha Verma', contact='9000000002'),
            Customer(name='Rohit Gupta', contact='9000000003'),
        ]
        db.session.add_all(custs)

    db.session.commit()


# ── Run the App ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()     # Create all tables
        seed_data()         # Add sample data
    app.run(debug=True, port=5000)
