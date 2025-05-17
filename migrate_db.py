from app import app, db
import models
import sqlite3
import os

def migrate_database():
    with app.app_context():
        # First create any missing tables
        db.create_all()
        
        # Get the database path
        db_path = os.path.join('instance', 'timetracker.db')
        
        # Now directly add the task_id column to time_entry if it doesn't exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if task_id column exists
        cursor.execute("PRAGMA table_info(time_entry)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'task_id' not in columns:
            print("Adding task_id column to time_entry table...")
            cursor.execute("ALTER TABLE time_entry ADD COLUMN task_id INTEGER REFERENCES task(id)")
            conn.commit()
            print("Column added successfully!")
        else:
            print("task_id column already exists.")
        
        conn.close()
        print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()