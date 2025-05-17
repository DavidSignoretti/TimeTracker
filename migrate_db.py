from app import app, db
import models

def migrate_database():
    with app.app_context():
        # This will create any missing tables and add missing columns
        db.create_all()
        
        print("Database schema updated successfully!")

if __name__ == "__main__":
    migrate_database()