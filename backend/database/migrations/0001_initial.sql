-- Initial schema for VisionAI. Stores metadata only; never video binaries.

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    folder_path TEXT NOT NULL,
    cache_path TEXT NOT NULL,
    exports_path TEXT NOT NULL,
    default_platform TEXT DEFAULT 'youtube',
    editing_style TEXT DEFAULT 'balanced',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version TEXT DEFAULT '1'
);

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT NOT NULL,
    hash TEXT,
    fingerprint TEXT,
    duration REAL DEFAULT 0,
    fps REAL DEFAULT 0,
    width INTEGER DEFAULT 0,
    height INTEGER DEFAULT 0,
    bitrate INTEGER DEFAULT 0,
    codec TEXT DEFAULT '',
    audio_codec TEXT DEFAULT '',
    has_audio INTEGER DEFAULT 0,
    file_size INTEGER DEFAULT 0,
    media_category TEXT DEFAULT 'raw',
    thumbnail_path TEXT,
    proxy_path TEXT,
    available INTEGER DEFAULT 1,
    analyzed INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    UNIQUE(project_id, path)
);

CREATE TABLE IF NOT EXISTS analysis_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,            -- pending | running | completed | failed | skipped
    progress REAL DEFAULT 0,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    model_version TEXT DEFAULT '',
    UNIQUE(video_id, stage)
);

CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    scene_number INTEGER NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    duration REAL NOT NULL,
    thumbnail_path TEXT
);

CREATE TABLE IF NOT EXISTS transcript_segments (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    speaker TEXT DEFAULT '',
    confidence REAL DEFAULT 0,
    text TEXT NOT NULL,
    language TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS frames (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp REAL NOT NULL,
    image_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS objects (
    id TEXT PRIMARY KEY,
    frame_id TEXT NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    confidence REAL DEFAULT 0,
    x REAL DEFAULT 0,
    y REAL DEFAULT 0,
    width REAL DEFAULT 0,
    height REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS quality_metrics (
    id TEXT PRIMARY KEY,
    frame_id TEXT NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
    brightness REAL DEFAULT 0,
    contrast REAL DEFAULT 0,
    blur_score REAL DEFAULT 0,
    noise_score REAL DEFAULT 0,
    sharpness REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audio_analysis (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp REAL NOT NULL,
    silence INTEGER DEFAULT 0,
    loudness REAL DEFAULT 0,
    peak REAL DEFAULT 0,
    background_noise REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,           -- transcript | scene | frame
    source_id TEXT NOT NULL,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    vector BLOB,                         -- stored vector (numpy float32)
    model_version TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS planner_sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    brief TEXT NOT NULL,
    script TEXT DEFAULT '',
    audience TEXT DEFAULT '',
    platform TEXT DEFAULT 'youtube',
    target_length TEXT DEFAULT '',
    style TEXT DEFAULT '',
    plan_json TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',       -- pending | completed | failed
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS planner_recommendations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES planner_sessions(id) ON DELETE CASCADE,
    recommendation TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    accepted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS timelines (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    session_id TEXT REFERENCES planner_sessions(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    fps REAL DEFAULT 30,
    duration REAL DEFAULT 0,
    timeline_json TEXT DEFAULT '',
    exported INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS timeline_clips (
    id TEXT PRIMARY KEY,
    timeline_id TEXT NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    track TEXT NOT NULL,
    source_start REAL NOT NULL,
    source_end REAL NOT NULL,
    timeline_start REAL NOT NULL,
    timeline_end REAL NOT NULL,
    order_index INTEGER NOT NULL,
    clip_type TEXT DEFAULT 'video',      -- video | broll | audio | subtitle
    transition TEXT DEFAULT 'hard_cut',
    label TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    video_id TEXT,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,                -- pending | running | completed | failed | cancelled
    progress REAL DEFAULT 0,
    payload TEXT DEFAULT '',
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS search_history (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Indexes on frequently queried fields.
CREATE INDEX IF NOT EXISTS idx_videos_project ON videos(project_id);
CREATE INDEX IF NOT EXISTS idx_videos_hash ON videos(hash);
CREATE INDEX IF NOT EXISTS idx_videos_path ON videos(path);
CREATE INDEX IF NOT EXISTS idx_scenes_video ON scenes(video_id);
CREATE INDEX IF NOT EXISTS idx_scenes_time ON scenes(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_transcript_video ON transcript_segments(video_id);
CREATE INDEX IF NOT EXISTS idx_transcript_time ON transcript_segments(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_objects_label ON objects(label);
CREATE INDEX IF NOT EXISTS idx_frames_video ON frames(video_id);
CREATE INDEX IF NOT EXISTS idx_analysis_video ON analysis_state(video_id);
CREATE INDEX IF NOT EXISTS idx_jobs_project_status ON jobs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_video ON jobs(video_id);
CREATE INDEX IF NOT EXISTS idx_timeline_clips_timeline ON timeline_clips(timeline_id);
CREATE INDEX IF NOT EXISTS idx_planner_sessions_project ON planner_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_video ON embeddings(video_id);

-- Full text search over transcript text.
CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
    segment_id UNINDEXED,
    video_id UNINDEXED,
    text,
    tokenize='porter unicode61'
);
