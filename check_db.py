import sqlite3
import os

def check_database(db_path):
    """Check the schema of a SQLite database"""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        print(f"\nDatabase: {db_path}")
        print(f"Found {len(tables)} tables:")
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"  Columns ({len(columns)}):")
            for column in columns:
                cid, name, type_, notnull, dflt_value, pk = column
                nullable = "NOT NULL" if notnull else "NULL"
                primary_key = "PRIMARY KEY" if pk else ""
                
                print(f"    {name}: {type_} {nullable} {primary_key}")
        
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

if __name__ == "__main__":
    # Check both database files
    db_paths = [
        os.path.join('instance', 'database.sqlite'),
        os.path.join('instance', 'timetracker.db')
    ]
    
    for db_path in db_paths:
        check_database(db_path)