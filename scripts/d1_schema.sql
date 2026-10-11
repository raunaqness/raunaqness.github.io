CREATE TABLE IF NOT EXISTS albums (
  slug TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  date TEXT,              -- "YYYY-MM", plain text, editable directly, no datetime bugs
  camera TEXT,
  lens TEXT,
  cover_key TEXT
);

CREATE TABLE IF NOT EXISTS photos (
  r2_key TEXT PRIMARY KEY,            -- stable key, e.g. "<slug>/<drive_file_id>.webp"
  album_slug TEXT NOT NULL REFERENCES albums(slug),
  drive_file_id TEXT NOT NULL,
  drive_modified_time TEXT NOT NULL,  -- used to detect "did this file change"
  width INTEGER,
  height INTEGER,
  sort_key TEXT NOT NULL              -- Drive createdTime, for ordering within the album
);

CREATE INDEX IF NOT EXISTS idx_photos_album ON photos(album_slug);
