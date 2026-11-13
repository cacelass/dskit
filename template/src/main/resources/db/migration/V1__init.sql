-- Migracion inicial del proyecto (Flyway).
-- El agente `migrations` es el unico dueno de db/migration/ (JAVA-007).
CREATE TABLE app_info (
    id BIGINT NOT NULL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
