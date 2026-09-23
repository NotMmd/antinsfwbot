PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS posts (
  chat_id TEXT NOT NULL,
  message_id INTEGER NOT NULL,
  date INTEGER NOT NULL,
  message_thread_id INTEGER,
  text TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS posts_latest_idx ON posts (date DESC, message_id DESC);

CREATE TABLE IF NOT EXISTS threads (
  chat_id TEXT NOT NULL,
  message_thread_id INTEGER NOT NULL,
  channel_chat_id TEXT NOT NULL,
  channel_post_message_id INTEGER NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (chat_id, message_thread_id)
);

CREATE TABLE IF NOT EXISTS join_messages (
  chat_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  message_id INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (chat_id, user_id, message_id)
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
