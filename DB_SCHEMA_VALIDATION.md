# Database Schema Validation

This document describes the database schema validation process for the TimeTracker application.

## Overview

The TimeTracker application uses SQLite databases to store data. The schema validation ensures that the database structure matches the expected schema defined in the application's models.

## Database Files

The application uses the following database files:

- `instance/timetracker.db`: The main database file used by the application
- `instance/database.sqlite`: An alternative database file (not actively used)

## Schema Validation

The schema validation process checks:

1. All expected tables exist in the database
2. All expected columns exist in each table
3. Column properties (type, nullable, primary key, foreign key) match the expected schema

## Validation Tools

### 1. migrate_db.py

The `migrate_db.py` script includes comprehensive schema validation and migration functionality:

```bash
python3 migrate_db.py
```

This script:
- Validates the database schema against the expected schema from models.py
- Automatically creates missing tables and columns
- Migrates data when necessary (e.g., hourly rates)

### 2. validate_db_schema.py

A standalone validation script that can be used to check the schema of any database file:

```bash
python3 validate_db_schema.py
```

This script:
- Checks both database files (timetracker.db and database.sqlite)
- Reports any schema issues found
- Can automatically fix schema issues

## Expected Schema

The expected schema is defined in `models.py` and includes the following tables:

1. `client`: Stores client information
2. `hourly_rate`: Stores hourly rates for clients
3. `time_entry`: Stores time tracking entries
4. `invoice`: Stores invoice information
5. `task`: Stores task information
6. `quote`: Stores quote information
7. `company_settings`: Stores company settings

## Validation Process

When the application starts or when the migration script is run, the following steps are performed:

1. The expected schema is extracted from the SQLAlchemy models
2. The actual schema is extracted from the database
3. The two schemas are compared to identify any discrepancies
4. If discrepancies are found, they are fixed automatically

## Manual Validation

To manually validate the database schema:

1. Run the validation script:
   ```bash
   python3 validate_db_schema.py
   ```

2. Review the output to see if any issues are found
3. If issues are found, they will be fixed automatically

## Troubleshooting

If you encounter database schema issues:

1. Ensure you're using the correct database file (timetracker.db)
2. Run the migration script to fix any schema issues:
   ```bash
   python3 migrate_db.py
   ```
3. If issues persist, you may need to recreate the database:
   ```bash
   rm instance/timetracker.db
   python3 migrate_db.py
   ```

## Conclusion

Regular schema validation ensures that the database structure remains consistent with the application's models, preventing data integrity issues and application errors.