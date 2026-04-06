# models.py - Database models for Cafe Management System
# Each class maps to a table in the SQLite database

from database import db
from datetime import datetime


# ─────────────────────────────────────────────
# Customer Model
# Stores customer name and contact info
# ─────────────────────────────────────────────
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One customer can have many orders
    orders = db.relationship('Order', backref='customer', lazy=True, cascade='all, delete')
    # One customer can have many reservations
    reservations = db.relationship('Reservation', backref='customer', lazy=True, cascade='all, delete')


# ─────────────────────────────────────────────
# Employee (Staff) Model
# Stores staff name, role and contact
# ─────────────────────────────────────────────
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)   # e.g. Waiter, Chef, Cashier
    contact = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One employee can process many orders
    # We will just let employee_id become NULL since it is nullable=True,
    # OR we can cascade delete the orders? Wait, we shouldn't delete orders 
    # when an employee is deleted. But if SQLAlchemy fails to set it to NULL automatically,
    # let's set lazy='dynamic' or just ignore? Actually, the default is save-update, merge. 
    # Let's leave it as is, or wait! If lazy=True, SQLAlchemy will update orders to set employee_id = NULL. 
    # Let's change backref to ensure it allows nulling out.
    orders = db.relationship('Order', backref='employee', lazy=True)


# ─────────────────────────────────────────────
# Menu Item Model
# Stores cafe items with price and category
# ─────────────────────────────────────────────
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)   # e.g. Drinks, Food, Desserts
    description = db.Column(db.String(200), default='')
    available = db.Column(db.Boolean, default=True)

    # One menu item can appear in many order items
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)


# ─────────────────────────────────────────────
# Order Model
# Tracks each customer order and its status
# ─────────────────────────────────────────────
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending')   # Pending, Preparing, Ready, Delivered, Cancelled

    # One order has many line items
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete')
    # One order has one payment
    payment = db.relationship('Payment', backref='order', uselist=False)


# ─────────────────────────────────────────────
# OrderItem Model
# Each line item in an order (menu item + qty)
# ─────────────────────────────────────────────
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    subtotal = db.Column(db.Float, default=0.0)


# ─────────────────────────────────────────────
# Reservation Model
# Table booking with date and guest count
# ─────────────────────────────────────────────
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    guest_count = db.Column(db.Integer, nullable=False)
    table_no = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Confirmed')   # Confirmed, Cancelled, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# Payment Model
# Records payment details for an order
# ─────────────────────────────────────────────
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), nullable=False)   # Cash, Card, UPI
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
