-- PostgreSQL Initialization Script for Lenox Cat Hospital
-- This script runs automatically when the database container is first created

-- Set timezone
SET timezone = 'America/New_York';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges to the application user
GRANT ALL PRIVILEGES ON DATABASE vet_clinic_db TO vet_clinic_user;

-- The actual tables will be created by Flask-Migrate (flask db upgrade)
-- This script just sets up the database basics
