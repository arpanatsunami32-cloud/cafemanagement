# database.py - Creates the SQLAlchemy instance
# Imported by both app.py and models.py to avoid circular imports

from flask_sqlalchemy import SQLAlchemy

# Single global db instance shared across the app
db = SQLAlchemy()
