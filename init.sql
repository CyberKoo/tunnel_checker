create table if not exists probe_history
(
    id        INTEGER NOT NULL PRIMARY KEY,
    min_rtt   FLOAT   NOT NULL,
    max_rtt   FLOAT   NOT NULL,
    sent      INTEGER NOT NULL,
    received  INTEGER NOT NULL,
    loss      FLOAT   NOT NULL,
    timestamp TEXT    NOT NULL
)