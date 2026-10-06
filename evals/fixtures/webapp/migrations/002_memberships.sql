CREATE TABLE memberships (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'member', 'viewer')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (team_id, user_id)
);

CREATE INDEX memberships_team_idx ON memberships (team_id);
