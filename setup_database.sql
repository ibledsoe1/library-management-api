-- Run with 'psql -U postgres -d postgres -f scripts/setup_database.sql'
SELECT 'CREATE ROLE postgres WITH LOGIN PASSWORD ''postgres'''
WHERE NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'postgres'
)
\gexec

SELECT 'CREATE DATABASE library OWNER postgres'
WHERE NOT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = 'library'
)
\gexec