# Alembic Database Migration Setup Guide

This guide explains how to use Alembic for database migrations in the Divine Whispers FastAPI project.

## 📋 Overview

Alembic has been successfully configured for the Divine Whispers project with:
- **Async SQLAlchemy support** for PostgreSQL
- **Environment variable integration** for database URLs
- **Complete initial migration** with all 6 database tables
- **Proper foreign key relationships** and indexes
- **Error handling** for both online and offline modes

## 🏗️ Database Schema

The initial migration creates the following tables:

1. **users** - User authentication and management
2. **wallets** - User point/credit balance management  
3. **transactions** - Financial transaction records
4. **jobs** - Background job processing
5. **job_results** - Job execution results and file storage
6. **audit_logs** - System activity and security logging

## 🚀 Quick Start

### 1. Prerequisites

Make sure you have the required packages installed:
```bash
cd Backend
pip install alembic asyncpg pydantic-settings
```

### 2. Environment Configuration

Create a `.env` file in the `Backend/` directory:
```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/divine_whispers

# Or use individual components (will be auto-assembled)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=divine_whispers
```

### 3. Apply Initial Migration

To create all database tables:
```bash
cd Backend
python -m alembic upgrade head
```

## 📝 Common Migration Commands

### Check Migration Status
```bash
# Show current migration version
python -m alembic current

# Show migration history
python -m alembic history --verbose
```

### Create New Migrations
```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "Description of changes"

# Create empty migration file
python -m alembic revision -m "Manual migration description"
```

### Apply Migrations
```bash
# Upgrade to latest version
python -m alembic upgrade head

# Upgrade to specific version
python -m alembic upgrade <revision_id>

# Upgrade by relative amount
python -m alembic upgrade +2  # upgrade 2 versions
```

### Rollback Migrations
```bash
# Downgrade by one version
python -m alembic downgrade -1

# Downgrade to specific version
python -m alembic downgrade <revision_id>

# Downgrade to base (remove all tables)
python -m alembic downgrade base
```

### Generate SQL Without Executing
```bash
# Preview SQL for upgrade
python -m alembic upgrade --sql head

# Preview SQL for downgrade
python -m alembic downgrade --sql -1
```

## 🛠️ Configuration Files

### Key Files Structure
```
Backend/
├── alembic.ini                 # Main configuration
├── alembic/
│   ├── env.py                  # Migration environment
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration files
│       └── 7d71d4f4f4fb_initial_migration_with_all_tables.py
├── app/
│   ├── core/
│   │   ├── config.py          # App configuration
│   │   └── database.py        # Database setup
│   └── models/                # SQLAlchemy models
└── requirements.txt
```

### Environment Variables Used
- `DATABASE_URL` - Complete database connection string
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Individual components
- `DEBUG` - Enables SQL query logging when True

## 🔧 Advanced Usage

### Working with Multiple Databases
The current setup supports a single PostgreSQL database. For multiple databases, you would need to:
1. Create separate Alembic configurations
2. Use multiple `alembic.ini` files
3. Configure different migration directories

### Custom Migration Operations
```python
# Example custom migration
def upgrade() -> None:
    # Create custom index
    op.create_index(
        'ix_custom_compound', 
        'table_name', 
        ['column1', 'column2']
    )
    
    # Execute raw SQL
    op.execute("UPDATE table_name SET column = 'value' WHERE condition")
```

### Performance Considerations
- **Indexes**: The initial migration includes optimized indexes for common queries
- **Foreign Keys**: Proper cascade rules are configured for data integrity
- **JSON Fields**: Used for flexible metadata storage with PostgreSQL JSON support

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Error: password authentication failed
# Solution: Check DATABASE_URL or individual DB_* variables in .env
```

**2. Import Errors**
```bash
# Error: ModuleNotFoundError
# Solution: Ensure you're running from the Backend/ directory
```

**3. Migration Conflicts**
```bash
# Error: Multiple head revisions
# Solution: Merge migrations or resolve conflicts
python -m alembic merge -m "merge conflicts" <revision1> <revision2>
```

### Development vs Production

**Development**:
- Use local PostgreSQL instance
- Enable DEBUG mode for SQL logging
- Test migrations thoroughly before applying to production

**Production**:
- Use environment variables for sensitive data
- Always backup database before migrations
- Consider using read replicas during migrations
- Test migrations on staging environment first

## 🔒 Security Notes

1. **Never commit database credentials** to version control
2. **Use environment variables** for all sensitive configuration
3. **Review auto-generated migrations** before applying
4. **Backup production databases** before running migrations
5. **Use proper database user permissions** for migration operations

## 📊 Migration Best Practices

### 1. Migration Safety
- Always review auto-generated migrations
- Test migrations on development data first
- Use transactions for complex migrations
- Plan rollback strategies

### 2. Performance
- Add indexes for new columns that will be queried
- Consider impact on large tables
- Use batch operations for data migrations
- Monitor query performance after schema changes

### 3. Collaboration
- Use descriptive migration messages
- Keep migrations small and focused
- Communicate schema changes to team members
- Document breaking changes

## 🎯 Next Steps

1. **Set up your database**: Create PostgreSQL database and user
2. **Configure environment**: Create `.env` file with database credentials
3. **Run initial migration**: Execute `alembic upgrade head`
4. **Verify setup**: Check that all tables are created successfully
5. **Start development**: Begin using the FastAPI application with database support

For more information, see the [Alembic documentation](https://alembic.sqlalchemy.org/) and [SQLAlchemy documentation](https://docs.sqlalchemy.org/).