-- PostgreSQL Initialization Script for Lenox Cat Hospital
-- This script runs automatically when the database container is first created
-- The database and user are automatically created by PostgreSQL's docker-entrypoint
-- using the POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD environment variables

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Lenox Cat Hospital Database Initialization';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'Current User: %', current_user();
    RAISE NOTICE 'Timezone: %', current_setting('timezone');
    RAISE NOTICE 'Extensions: uuid-ossp, pg_trgm';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Application tables will be created by Flask-Migrate';
    RAISE NOTICE '========================================';
END $$;

-- Note: Additional database setup can be added here if needed
-- The actual application tables will be created by Flask-Migrate (flask db upgrade)
-- This script only sets up extensions and basic database configuration
