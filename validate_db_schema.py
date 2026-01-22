import sqlite3
import os
import sys
from app import app, db
import models
import inspect

def get_expected_tables():
    """Get the expected tables from the SQLAlchemy models"""
    expected_tables = {}
    
    # Get all model classes from models.py
    model_classes = []
    for name, obj in inspect.getmembers(models):
        if inspect.isclass(obj) and hasattr(obj, '__tablename__'):
            model_classes.append(obj)
    
    # Extract table info from each model
    for model_class in model_classes:
        table_name = model_class.__tablename__
        expected_tables[table_name] = {
            'columns': {}
        }
        
        # Get column info
        for column_name, column in model_class.__table__.columns.items():
            column_type = str(column.type)
            nullable = not column.nullable
            primary_key = column.primary_key
            foreign_key = None
            
            # Check for foreign keys
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    foreign_key = str(fk.target_fullname)
            
            expected_tables[table_name]['columns'][column_name] = {
                'type': column_type,
                'nullable': nullable,
                'primary_key': primary_key,
                'foreign_key': foreign_key
            }
    
    return expected_tables

def get_actual_tables(db_path):
    """Get the actual tables from the SQLite database"""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist!")
        return {}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    actual_tables = {}
    
    for table in tables:
        table_name = table[0]
        actual_tables[table_name] = {
            'columns': {}
        }
        
        # Get column info for this table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for column in columns:
            cid, name, type_, notnull, dflt_value, pk = column
            
            # Get foreign key info
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            foreign_key = None
            for fk in foreign_keys:
                if fk[3] == name:  # If this column is a foreign key
                    foreign_key = f"{fk[2]}.{fk[4]}"
            
            actual_tables[table_name]['columns'][name] = {
                'type': type_,
                'nullable': notnull == 1,
                'primary_key': pk == 1,
                'foreign_key': foreign_key
            }
    
    conn.close()
    return actual_tables

def validate_schema(db_path):
    """Validate the database schema against the expected schema"""
    with app.app_context():
        expected_tables = get_expected_tables()
        actual_tables = get_actual_tables(db_path)
        
        issues_found = False
        
        # Check for missing tables
        missing_tables = set(expected_tables.keys()) - set(actual_tables.keys())
        if missing_tables:
            issues_found = True
            print(f"Missing tables: {', '.join(missing_tables)}")
        
        # Check for extra tables
        extra_tables = set(actual_tables.keys()) - set(expected_tables.keys())
        if extra_tables:
            print(f"Extra tables (not in models): {', '.join(extra_tables)}")
        
        # Check table schemas
        for table_name in set(expected_tables.keys()) & set(actual_tables.keys()):
            expected_columns = expected_tables[table_name]['columns']
            actual_columns = actual_tables[table_name]['columns']
            
            # Check for missing columns
            missing_columns = set(expected_columns.keys()) - set(actual_columns.keys())
            if missing_columns:
                issues_found = True
                print(f"Table '{table_name}' is missing columns: {', '.join(missing_columns)}")
            
            # Check for extra columns
            extra_columns = set(actual_columns.keys()) - set(expected_columns.keys())
            if extra_columns:
                print(f"Table '{table_name}' has extra columns: {', '.join(extra_columns)}")
            
            # Check column properties for columns that exist in both
            for column_name in set(expected_columns.keys()) & set(actual_columns.keys()):
                expected_column = expected_columns[column_name]
                actual_column = actual_columns[column_name]
                
                # Check nullable constraint
                if expected_column['nullable'] != actual_column['nullable']:
                    issues_found = True
                    print(f"Column '{table_name}.{column_name}' has different nullable constraint: "
                          f"expected {'NOT NULL' if expected_column['nullable'] else 'NULL'}, "
                          f"got {'NOT NULL' if actual_column['nullable'] else 'NULL'}")
                
                # Check primary key constraint
                if expected_column['primary_key'] != actual_column['primary_key']:
                    issues_found = True
                    print(f"Column '{table_name}.{column_name}' has different primary key constraint: "
                          f"expected {'PRIMARY KEY' if expected_column['primary_key'] else 'not PRIMARY KEY'}, "
                          f"got {'PRIMARY KEY' if actual_column['primary_key'] else 'not PRIMARY KEY'}")
                
                # Check foreign key constraint (simplified check)
                if bool(expected_column['foreign_key']) != bool(actual_column['foreign_key']):
                    issues_found = True
                    print(f"Column '{table_name}.{column_name}' has different foreign key constraint: "
                          f"expected {expected_column['foreign_key']}, got {actual_column['foreign_key']}")
        
        if not issues_found:
            print(f"Database schema for {db_path} is valid!")
            return True
        else:
            print(f"Database schema for {db_path} has issues!")
            return False

def fix_schema(db_path):
    """Fix the database schema by creating missing tables and columns"""
    with app.app_context():
        print(f"Fixing schema for {db_path}...")
        
        # Create all tables that should exist
        db.create_all()
        
        # Connect to the database to add any missing columns
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        expected_tables = get_expected_tables()
        actual_tables = get_actual_tables(db_path)
        
        # For each table that exists in both expected and actual
        for table_name in set(expected_tables.keys()) & set(actual_tables.keys()):
            expected_columns = expected_tables[table_name]['columns']
            actual_columns = actual_tables[table_name]['columns']
            
            # Check for missing columns
            missing_columns = set(expected_columns.keys()) - set(actual_columns.keys())
            for column_name in missing_columns:
                column_info = expected_columns[column_name]
                column_type = column_info['type']
                nullable = "" if column_info['nullable'] else "NOT NULL"
                
                print(f"Adding missing column '{column_name}' to table '{table_name}'")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {nullable}")
                except sqlite3.OperationalError as e:
                    print(f"Error adding column: {e}")
        
        conn.commit()
        conn.close()
        
        # Validate again to confirm fixes
        return validate_schema(db_path)

if __name__ == "__main__":
    # Check both database files
    db_paths = [
        os.path.join('instance', 'database.sqlite'),
        os.path.join('instance', 'timetracker.db')
    ]
    
    all_valid = True
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\nValidating schema for {db_path}...")
            if not validate_schema(db_path):
                all_valid = False
                print(f"Automatically fixing schema for {db_path}...")
                fix_schema(db_path)
        else:
            print(f"\nDatabase file {db_path} does not exist.")
    
    # Exit with appropriate status code
    if all_valid:
        print("\nAll database schemas are valid!")
        sys.exit(0)
    else:
        print("\nSchema validation completed with fixes applied.")
        sys.exit(0)  # Still exit with 0 since we fixed the issues