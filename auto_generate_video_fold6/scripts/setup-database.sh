#!/bin/bash

# Database Setup and Migration Script
# This script initializes the database, runs migrations, and seeds data

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-auto_video_db}"
DB_USER="${POSTGRES_USER:-auto_video_user}"
DB_PASSWORD="${POSTGRES_PASSWORD:-your_secure_password_here}"

echo -e "${BLUE}🚀 Auto Video Generation System - Database Setup${NC}"
echo "================================================="

# Function to check if PostgreSQL is running
check_postgres() {
    echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
    
    for i in {1..30}; do
        if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL is running${NC}"
            return 0
        fi
        echo "Waiting for PostgreSQL... ($i/30)"
        sleep 2
    done
    
    echo -e "${RED}✗ Failed to connect to PostgreSQL${NC}"
    exit 1
}

# Function to create database if it doesn't exist
create_database() {
    echo -e "${YELLOW}Creating database if not exists...${NC}"
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "
    SELECT 'CREATE DATABASE $DB_NAME' 
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
    " >/dev/null 2>&1
    
    echo -e "${GREEN}✓ Database ready${NC}"
}

# Function to enable extensions
enable_extensions() {
    echo -e "${YELLOW}Enabling PostgreSQL extensions...${NC}"
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
    CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";
    CREATE EXTENSION IF NOT EXISTS \"btree_gin\";
    "
    
    echo -e "${GREEN}✓ Extensions enabled${NC}"
}

# Function to run Alembic migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    
    cd services/auth-service
    
    # Set database URL for Alembic
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Install requirements if needed
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    else
        source venv/bin/activate
    fi
    
    # Run migrations
    alembic upgrade head
    
    deactivate
    cd ../..
    
    echo -e "${GREEN}✓ Migrations completed${NC}"
}

# Function to seed data
seed_data() {
    echo -e "${YELLOW}Seeding database with initial data...${NC}"
    
    # Run seed files in order
    for seed_file in database/seeds/*.sql; do
        if [ -f "$seed_file" ]; then
            echo "Running $(basename "$seed_file")..."
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$seed_file"
        fi
    done
    
    echo -e "${GREEN}✓ Data seeding completed${NC}"
}

# Function to verify setup
verify_setup() {
    echo -e "${YELLOW}Verifying database setup...${NC}"
    
    # Check if tables exist
    table_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    " | xargs)
    
    echo "Tables created: $table_count"
    
    # Check if users exist
    user_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) FROM users;
    " | xargs)
    
    echo "Users created: $user_count"
    
    # Check if sample projects exist
    project_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) FROM video_projects;
    " | xargs)
    
    echo "Sample projects: $project_count"
    
    if [ "$table_count" -gt 10 ] && [ "$user_count" -gt 0 ]; then
        echo -e "${GREEN}✓ Database setup verification passed${NC}"
    else
        echo -e "${RED}✗ Database setup verification failed${NC}"
        exit 1
    fi
}

# Function to create backup
create_backup() {
    echo -e "${YELLOW}Creating database backup...${NC}"
    
    mkdir -p backups
    backup_file="backups/initial_setup_$(date +%Y%m%d_%H%M%S).sql"
    
    PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME > "$backup_file"
    
    echo -e "${GREEN}✓ Backup created: $backup_file${NC}"
}

# Function to show connection info
show_connection_info() {
    echo -e "${BLUE}📊 Database Connection Information${NC}"
    echo "=================================="
    echo "Host: $DB_HOST"
    echo "Port: $DB_PORT"
    echo "Database: $DB_NAME"
    echo "User: $DB_USER"
    echo ""
    echo -e "${BLUE}📝 Default Login Credentials${NC}"
    echo "============================"
    echo "Admin User:"
    echo "  Email: admin@autovideo.com"
    echo "  Username: admin"
    echo "  Password: admin123456"
    echo ""
    echo "Demo Creator:"
    echo "  Email: creator@autovideo.com"
    echo "  Username: demo_creator"
    echo "  Password: creator123"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Change these passwords in production!${NC}"
}

# Main execution
main() {
    case "${1:-setup}" in
        "setup")
            check_postgres
            create_database
            enable_extensions
            run_migrations
            seed_data
            verify_setup
            create_backup
            show_connection_info
            echo -e "${GREEN}🎉 Database setup completed successfully!${NC}"
            ;;
        "migrate")
            check_postgres
            run_migrations
            echo -e "${GREEN}✓ Migrations completed${NC}"
            ;;
        "seed")
            check_postgres
            seed_data
            echo -e "${GREEN}✓ Data seeding completed${NC}"
            ;;
        "verify")
            check_postgres
            verify_setup
            ;;
        "backup")
            check_postgres
            create_backup
            ;;
        "reset")
            echo -e "${RED}⚠️  This will DROP the entire database and recreate it!${NC}"
            read -p "Are you sure? (type 'yes' to confirm): " confirm
            if [ "$confirm" = "yes" ]; then
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
                echo -e "${YELLOW}Database dropped. Running full setup...${NC}"
                "$0" setup
            else
                echo "Reset cancelled."
            fi
            ;;
        *)
            echo "Usage: $0 {setup|migrate|seed|verify|backup|reset}"
            echo ""
            echo "Commands:"
            echo "  setup   - Full database setup (migrations + seeding)"
            echo "  migrate - Run migrations only"
            echo "  seed    - Run data seeding only"
            echo "  verify  - Verify database setup"
            echo "  backup  - Create database backup"
            echo "  reset   - Drop and recreate database (DANGEROUS)"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"