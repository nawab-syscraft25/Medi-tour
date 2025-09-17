#!/bin/bash

# Database export/restore scripts for PostgreSQL and MySQL
# Usage: ./export_db.sh [export|import] [postgresql|mysql] [additional_args...]

set -e

# Source environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

COMMAND=$1
DB_TYPE=$2

if [ -z "$COMMAND" ] || [ -z "$DB_TYPE" ]; then
    echo "Usage: $0 [export|import] [postgresql|mysql] [additional_args...]"
    echo ""
    echo "Examples:"
    echo "  $0 export postgresql"
    echo "  $0 import postgresql backup.sql"
    echo "  $0 export mysql"
    echo "  $0 import mysql backup.sql"
    exit 1
fi

# Parse DATABASE_URL to extract connection details
parse_database_url() {
    # Extract components from DATABASE_URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    # or: mysql+aiomysql://user:pass@host:port/dbname
    
    # Remove the protocol part
    DB_URL_CLEAN=$(echo $DATABASE_URL | sed 's/.*:\/\///')
    
    # Extract user:pass@host:port/dbname
    DB_USER=$(echo $DB_URL_CLEAN | cut -d: -f1)
    DB_PASS_HOST=$(echo $DB_URL_CLEAN | cut -d: -f2-)
    DB_PASS=$(echo $DB_PASS_HOST | cut -d@ -f1)
    DB_HOST_PORT_DB=$(echo $DB_PASS_HOST | cut -d@ -f2)
    DB_HOST=$(echo $DB_HOST_PORT_DB | cut -d: -f1)
    DB_PORT_DB=$(echo $DB_HOST_PORT_DB | cut -d: -f2)
    DB_PORT=$(echo $DB_PORT_DB | cut -d/ -f1)
    DB_NAME=$(echo $DB_PORT_DB | cut -d/ -f2)
    
    echo "Parsed connection details:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  User: $DB_USER"
    echo "  Database: $DB_NAME"
}

export_postgresql() {
    echo "🗄️  Exporting PostgreSQL database..."
    parse_database_url
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="meditour_postgresql_${TIMESTAMP}.sql"
    
    echo "Creating SQL dump: $BACKUP_FILE"
    PGPASSWORD=$DB_PASS pg_dump \
        -h $DB_HOST \
        -p $DB_PORT \
        -U $DB_USER \
        -d $DB_NAME \
        --no-password \
        --verbose \
        --clean \
        --if-exists \
        > $BACKUP_FILE
    
    echo "✅ PostgreSQL export completed: $BACKUP_FILE"
    
    # Also create a custom format backup
    CUSTOM_BACKUP="meditour_postgresql_${TIMESTAMP}.dump"
    echo "Creating custom format backup: $CUSTOM_BACKUP"
    PGPASSWORD=$DB_PASS pg_dump \
        -h $DB_HOST \
        -p $DB_PORT \
        -U $DB_USER \
        -d $DB_NAME \
        --no-password \
        -F custom \
        -b \
        -v \
        $CUSTOM_BACKUP
    
    echo "✅ Custom format backup completed: $CUSTOM_BACKUP"
}

import_postgresql() {
    BACKUP_FILE=$3
    if [ -z "$BACKUP_FILE" ]; then
        echo "❌ Please specify backup file to import"
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    echo "🗄️  Importing PostgreSQL database from: $BACKUP_FILE"
    parse_database_url
    
    # Check if it's a custom format backup
    if [[ $BACKUP_FILE == *.dump ]]; then
        echo "Importing custom format backup..."
        PGPASSWORD=$DB_PASS pg_restore \
            -h $DB_HOST \
            -p $DB_PORT \
            -U $DB_USER \
            -d $DB_NAME \
            --no-password \
            --verbose \
            --clean \
            --if-exists \
            $BACKUP_FILE
    else
        echo "Importing SQL backup..."
        PGPASSWORD=$DB_PASS psql \
            -h $DB_HOST \
            -p $DB_PORT \
            -U $DB_USER \
            -d $DB_NAME \
            --no-password \
            -f $BACKUP_FILE
    fi
    
    echo "✅ PostgreSQL import completed"
}

export_mysql() {
    echo "🗄️  Exporting MySQL database..."
    parse_database_url
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="meditour_mysql_${TIMESTAMP}.sql"
    
    echo "Creating SQL dump: $BACKUP_FILE"
    mysqldump \
        -h $DB_HOST \
        -P $DB_PORT \
        -u $DB_USER \
        -p$DB_PASS \
        --single-transaction \
        --routines \
        --triggers \
        --add-drop-database \
        --databases $DB_NAME \
        > $BACKUP_FILE
    
    echo "✅ MySQL export completed: $BACKUP_FILE"
}

import_mysql() {
    BACKUP_FILE=$3
    if [ -z "$BACKUP_FILE" ]; then
        echo "❌ Please specify backup file to import"
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    echo "🗄️  Importing MySQL database from: $BACKUP_FILE"
    parse_database_url
    
    mysql \
        -h $DB_HOST \
        -P $DB_PORT \
        -u $DB_USER \
        -p$DB_PASS \
        < $BACKUP_FILE
    
    echo "✅ MySQL import completed"
}

# Main execution
case "$DB_TYPE" in
    "postgresql")
        case "$COMMAND" in
            "export")
                export_postgresql
                ;;
            "import")
                import_postgresql "$@"
                ;;
            *)
                echo "❌ Invalid command: $COMMAND"
                exit 1
                ;;
        esac
        ;;
    "mysql")
        case "$COMMAND" in
            "export")
                export_mysql
                ;;
            "import")
                import_mysql "$@"
                ;;
            *)
                echo "❌ Invalid command: $COMMAND"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "❌ Invalid database type: $DB_TYPE"
        echo "Supported types: postgresql, mysql"
        exit 1
        ;;
esac