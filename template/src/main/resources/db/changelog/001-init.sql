-- liquibase formatted sql
-- changeset dskit:001-init
CREATE TABLE app_info (
    id BIGINT NOT NULL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- rollback DROP TABLE app_info;
