-- 007_resolution_cache.sql
-- parse_cache에 해상도 캐시 컬럼을 추가한다.

ALTER TABLE parse_cache ADD COLUMN resolution_value TEXT;
ALTER TABLE parse_cache ADD COLUMN resolution_source TEXT;
ALTER TABLE parse_cache ADD COLUMN resolution_signature TEXT;
