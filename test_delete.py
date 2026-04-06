from app import app, db
from models import Employee, Customer

with app.app_context():
    # Attempt to delete first employee
    emp = Employee.query.first()
    if emp:
        print(f"Deleting Employee: {emp.name}")
        db.session.delete(emp)
        try:
            db.session.commit()
            print("Employee deleted successfully.")
        except Exception as e:
            db.session.rollback()
            print("Failed to delete Employee:", e)
    else:
        print("No Employee found.")
    
    # Attempt to delete first customer
    cust = Customer.query.first()
    if cust:
        print(f"Deleting Customer: {cust.name}")
        db.session.delete(cust)
        try:
            db.session.commit()
            print("Customer deleted successfully.")
        except Exception as e:
            db.session.rollback()
            print("Failed to delete Customer:", e)
    else:
        print("No Customer found.")
