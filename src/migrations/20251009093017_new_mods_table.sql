-- +goose Up
-- +goose StatementBegin
DO $$ BEGIN
    CREATE TYPE mod_status AS ENUM ('UPLOADING', 'UPLOADED', 'FAILED', 'HIDDEN', 'BANNED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS mods (
    id SERIAL PRIMARY KEY,
    author_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    version INT NOT NULL DEFAULT 1,
    s3_key VARCHAR(255),
    status mod_status NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS mods;
DROP TYPE IF EXISTS mod_status;
-- +goose StatementEnd
