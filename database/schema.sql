CREATE TABLE clients (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE bot_connections (
  client_id TEXT NOT NULL,
  token TEXT NOT NULL,
  status TEXT NOT NULL,
  connected_at TEXT,
  disconnected_at TEXT,
  FOREIGN KEY (client_id) REFERENCES clients(id)
);
