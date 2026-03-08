-- +goose Up
-- +goose StatementBegin

-- Add ON_MODERATION to existing mod_status enum
ALTER TYPE mod_status ADD VALUE IF NOT EXISTS 'ON_MODERATION';

-- Update existing UPLOADING mods to ON_MODERATION
UPDATE mods SET status = 'ON_MODERATION' WHERE status = 'UPLOADING';

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin

-- Revert ON_MODERATION mods back to UPLOADING
UPDATE mods SET status = 'UPLOADING' WHERE status = 'ON_MODERATION';

-- Note: PostgreSQL does not support removing enum values directly
-- If rollback is needed, the enum type would need to be recreated
-- For now, we just revert the data changes

-- +goose StatementEnd
