"""Repository layer: the only place that executes SQL.

Each domain area has repository methods. Modules use these instead of raw
SQL, preserving the single-source-of-truth rule from 03-database.md.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

from backend.database.connection import Database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


class Repository:
    """Aggregate repository over a project database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ---- Pass-through query helpers (for ad-hoc SQL in pipeline/search) --
    def execute(self, sql: str, params: tuple = ()) -> Any:
        return self.db.execute(sql, params)

    def query_one(self, sql: str, params: tuple = ()) -> Any:
        return self.db.query_one(sql, params)

    def query_all(self, sql: str, params: tuple = ()) -> list[Any]:
        return [dict(r) for r in self.db.query_all(sql, params)]

    # ---- Projects -------------------------------------------------------
    def create_project(self, *, id: str, name: str, description: str,
                       folder_path: str, cache_path: str, exports_path: str,
                       default_platform: str = "youtube",
                       editing_style: str = "balanced") -> dict[str, Any]:
        now = _now()
        self.db.execute(
            """INSERT INTO projects (id, name, description, folder_path, cache_path,
               exports_path, default_platform, editing_style, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?);""",
            (id, name, description, folder_path, cache_path, exports_path,
             default_platform, editing_style, now, now),
        )
        return self.get_project(id)

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM projects WHERE id = ?;", (project_id,))
        return dict(row) if row else None

    def list_projects(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all("SELECT * FROM projects ORDER BY created_at DESC;")]

    def delete_project(self, project_id: str) -> None:
        self.db.execute("DELETE FROM projects WHERE id = ?;", (project_id,))

    # ---- Videos ---------------------------------------------------------
    def upsert_video(self, *, project_id: str, path: str, filename: str,
                     extension: str, **fields) -> dict[str, Any]:
        existing = self.db.query_one(
            "SELECT * FROM videos WHERE project_id = ? AND path = ?;",
            (project_id, path),
        )
        if existing:
            return dict(existing)
        vid = _uuid()
        now = _now()
        cols = {
            "id": vid, "project_id": project_id, "path": path, "filename": filename,
            "extension": extension, "hash": fields.get("hash"),
            "fingerprint": fields.get("fingerprint"),
            "duration": fields.get("duration", 0), "fps": fields.get("fps", 0),
            "width": fields.get("width", 0), "height": fields.get("height", 0),
            "bitrate": fields.get("bitrate", 0), "codec": fields.get("codec", ""),
            "audio_codec": fields.get("audio_codec", ""),
            "has_audio": 1 if fields.get("has_audio") else 0,
            "file_size": fields.get("file_size", 0),
            "media_category": fields.get("media_category", "raw"),
            "thumbnail_path": fields.get("thumbnail_path"),
            "proxy_path": fields.get("proxy_path"),
            "available": 1, "analyzed": 0, "created_at": now, "modified_at": now,
        }
        placeholders = ", ".join("?" * len(cols))
        self.db.execute(
            f"INSERT INTO videos ({', '.join(cols)}) VALUES ({placeholders});",
            tuple(cols.values()),
        )
        return self.get_video(vid)

    def get_video(self, video_id: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM videos WHERE id = ?;", (video_id,))
        return dict(row) if row else None

    def get_video_by_path(self, project_id: str, path: str) -> dict[str, Any] | None:
        row = self.db.query_one(
            "SELECT * FROM videos WHERE project_id = ? AND path = ?;",
            (project_id, path),
        )
        return dict(row) if row else None

    def list_videos(self, project_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM videos WHERE project_id = ? ORDER BY filename;",
            (project_id,),
        )]

    def update_video(self, video_id: str, **fields) -> None:
        if not fields:
            return
        fields["modified_at"] = _now()
        assignments = ", ".join(f"{k} = ?" for k in fields)
        self.db.execute(
            f"UPDATE videos SET {assignments} WHERE id = ?;",
            tuple(fields.values()) + (video_id,),
        )

    def set_video_unavailable(self, video_id: str) -> None:
        self.update_video(video_id, available=0)

    # ---- Analysis state -------------------------------------------------
    def get_analysis_state(self, video_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM analysis_state WHERE video_id = ?;", (video_id,),
        )]

    def get_stage_status(self, video_id: str, stage: str) -> str | None:
        row = self.db.query_one(
            "SELECT status FROM analysis_state WHERE video_id = ? AND stage = ?;",
            (video_id, stage),
        )
        return row["status"] if row else None

    def set_stage_status(self, video_id: str, stage: str, status: str,
                         *, progress: float = 0, error: str | None = None,
                         model_version: str = "") -> None:
        self.db.execute(
            """INSERT INTO analysis_state (video_id, stage, status, progress, error,
               started_at, completed_at, model_version)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(video_id, stage) DO UPDATE SET
                 status=excluded.status,
                 progress=excluded.progress,
                 error=excluded.error,
                 started_at=CASE WHEN excluded.status='running' THEN ?
                                 ELSE analysis_state.started_at END,
                 completed_at=CASE WHEN excluded.status IN ('completed','failed','skipped')
                                   THEN ? ELSE analysis_state.completed_at END,
                 model_version=excluded.model_version;""",
            (video_id, stage, status, progress, error,
             _now() if status == "running" else None,
             _now() if status in ("completed", "failed", "skipped") else None,
             model_version,
             _now() if status == "running" else None,
             _now() if status in ("completed", "failed", "skipped") else None),
        )

    def increment_retry(self, video_id: str, stage: str) -> int:
        self.db.execute(
            "UPDATE analysis_state SET retry_count = retry_count + 1 WHERE video_id = ? AND stage = ?;",
            (video_id, stage),
        )
        row = self.db.query_one(
            "SELECT retry_count FROM analysis_state WHERE video_id = ? AND stage = ?;",
            (video_id, stage),
        )
        return int(row["retry_count"]) if row else 0

    # ---- Scenes ---------------------------------------------------------
    def add_scene(self, *, video_id: str, scene_number: int, start_time: float,
                  end_time: float, thumbnail_path: str | None = None) -> str:
        sid = _uuid()
        self.db.execute(
            """INSERT INTO scenes (id, video_id, scene_number, start_time, end_time,
               duration, thumbnail_path) VALUES (?,?,?,?,?,?,?);""",
            (sid, video_id, scene_number, start_time, end_time,
             end_time - start_time, thumbnail_path),
        )
        return sid

    def clear_scenes(self, video_id: str) -> None:
        self.db.execute("DELETE FROM scenes WHERE video_id = ?;", (video_id,))

    def list_scenes(self, video_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM scenes WHERE video_id = ? ORDER BY scene_number;",
            (video_id,),
        )]

    # ---- Transcript segments -------------------------------------------
    def add_transcript_segment(self, *, video_id: str, start_time: float,
                               end_time: float, text: str, confidence: float = 0,
                               speaker: str = "", language: str = "") -> str:
        sid = _uuid()
        self.db.execute(
            """INSERT INTO transcript_segments (id, video_id, start_time, end_time,
               speaker, confidence, text, language) VALUES (?,?,?,?,?,?,?,?);""",
            (sid, video_id, start_time, end_time, speaker, confidence, text, language),
        )
        # Keep FTS in sync.
        self.db.execute(
            "INSERT INTO transcript_fts (segment_id, video_id, text) VALUES (?,?,?);",
            (sid, video_id, text),
        )
        return sid

    def clear_transcript(self, video_id: str) -> None:
        segs = self.db.query_all(
            "SELECT id FROM transcript_segments WHERE video_id = ?;", (video_id,))
        if segs:
            placeholders = ",".join("?" * len(segs))
            self.db.execute(
                f"DELETE FROM transcript_fts WHERE segment_id IN ({placeholders});",
                tuple(r["id"] for r in segs),
            )
        self.db.execute("DELETE FROM transcript_segments WHERE video_id = ?;", (video_id,))

    def list_transcript(self, video_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM transcript_segments WHERE video_id = ? ORDER BY start_time;",
            (video_id,),
        )]

    def search_transcript_fts(self, project_id: str, query: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            """SELECT ts.id, ts.video_id, ts.start_time, ts.end_time, ts.text,
               ts.speaker, ts.confidence, ts.language, f.rank,
               v.filename, v.path
               FROM transcript_fts f
               JOIN transcript_segments ts ON ts.id = f.segment_id
               JOIN videos v ON v.id = ts.video_id
               WHERE v.project_id = ? AND transcript_fts MATCH ?
               ORDER BY f.rank LIMIT ?;""",
            (project_id, query, limit),
        )
        return [dict(r) for r in rows]

    # ---- Frames / objects / quality ------------------------------------
    def add_frame(self, *, video_id: str, timestamp: float, image_path: str) -> str:
        fid = _uuid()
        self.db.execute(
            "INSERT INTO frames (id, video_id, timestamp, image_path) VALUES (?,?,?,?);",
            (fid, video_id, timestamp, image_path),
        )
        return fid

    def clear_frames(self, video_id: str) -> None:
        self.db.execute("DELETE FROM frames WHERE video_id = ?;", (video_id,))

    def list_frames(self, video_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM frames WHERE video_id = ? ORDER BY timestamp;", (video_id,))]

    def add_object(self, *, frame_id: str, label: str, confidence: float = 0,
                   x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> str:
        oid = _uuid()
        self.db.execute(
            """INSERT INTO objects (id, frame_id, label, confidence, x, y, width, height)
               VALUES (?,?,?,?,?,?,?,?);""",
            (oid, frame_id, label, confidence, x, y, width, height),
        )
        return oid

    def list_objects_for_video(self, video_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            """SELECT o.* FROM objects o JOIN frames f ON f.id = o.frame_id
               WHERE f.video_id = ?;""", (video_id,))]

    def add_quality(self, *, frame_id: str, brightness: float, contrast: float,
                    blur_score: float, noise_score: float, sharpness: float) -> str:
        qid = _uuid()
        self.db.execute(
            """INSERT INTO quality_metrics (id, frame_id, brightness, contrast,
               blur_score, noise_score, sharpness) VALUES (?,?,?,?,?,?,?);""",
            (qid, frame_id, brightness, contrast, blur_score, noise_score, sharpness),
        )
        return qid

    # ---- Audio analysis -------------------------------------------------
    def add_audio_analysis(self, *, video_id: str, timestamp: float, silence: bool,
                           loudness: float, peak: float, background_noise: float) -> str:
        aid = _uuid()
        self.db.execute(
            """INSERT INTO audio_analysis (id, video_id, timestamp, silence, loudness,
               peak, background_noise) VALUES (?,?,?,?,?,?,?);""",
            (aid, video_id, timestamp, 1 if silence else 0, loudness, peak, background_noise),
        )
        return aid

    def clear_audio_analysis(self, video_id: str) -> None:
        self.db.execute("DELETE FROM audio_analysis WHERE video_id = ?;", (video_id,))

    # ---- Embeddings -----------------------------------------------------
    def add_embedding(self, *, source_type: str, source_id: str, video_id: str,
                      vector: bytes, model_version: str = "") -> str:
        eid = _uuid()
        self.db.execute(
            """INSERT INTO embeddings (id, source_type, source_id, video_id, vector,
               model_version, created_at) VALUES (?,?,?,?,?,?,?);""",
            (eid, source_type, source_id, video_id, vector, model_version, _now()),
        )
        return eid

    def list_embeddings(self, video_id: str | None = None,
                        source_type: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM embeddings"
        conditions: list[str] = []
        params: list[Any] = []
        if video_id:
            conditions.append("video_id = ?")
            params.append(video_id)
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        return [dict(r) for r in self.db.query_all(query + ";", tuple(params))]

    # ---- Jobs -----------------------------------------------------------
    def create_job(self, *, project_id: str, job_type: str, video_id: str | None = None,
                   payload: dict | None = None) -> str:
        jid = _uuid()
        self.db.execute(
            """INSERT INTO jobs (id, project_id, video_id, job_type, status, progress,
               payload, created_at) VALUES (?,?,?,?,?,?,?,?);""",
            (jid, project_id, video_id, job_type, "pending", 0,
             json.dumps(payload or {}), _now()),
        )
        return jid

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM jobs WHERE id = ?;", (job_id,))
        if row:
            d = dict(row)
            d["payload"] = json.loads(d["payload"] or "{}")
            return d
        return None

    def list_jobs(self, project_id: str, status: str | None = None,
                  limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM jobs WHERE project_id = ?"
        params: list[Any] = [project_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = [dict(r) for r in self.db.query_all(query + ";", tuple(params))]
        for r in rows:
            r["payload"] = json.loads(r["payload"] or "{}")
        return rows

    def claim_next_job(self, project_id: str) -> dict[str, Any] | None:
        """Atomically claim the next pending job (single heavy worker)."""
        row = self.db.query_one(
            """SELECT * FROM jobs WHERE project_id = ? AND status = 'pending'
               ORDER BY created_at ASC LIMIT 1;""",
            (project_id,),
        )
        if not row:
            return None
        self.db.execute(
            "UPDATE jobs SET status = 'running', started_at = ? WHERE id = ?;",
            (_now(), row["id"]),
        )
        d = dict(row)
        d["status"] = "running"
        d["started_at"] = _now()
        d["payload"] = json.loads(d["payload"] or "{}")
        return d

    def update_job(self, job_id: str, *, status: str | None = None,
                   progress: float | None = None, error: str | None = None) -> None:
        sets: list[str] = []
        params: list[Any] = []
        if status is not None:
            sets.append("status = ?")
            params.append(status)
            if status in ("completed", "failed", "cancelled"):
                sets.append("completed_at = ?")
                params.append(_now())
        if progress is not None:
            sets.append("progress = ?")
            params.append(progress)
        if error is not None:
            sets.append("error = ?")
            params.append(error)
        if not sets:
            return
        params.append(job_id)
        self.db.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id = ?;", tuple(params))

    # ---- Planner sessions ----------------------------------------------
    def create_planner_session(self, *, project_id: str, brief: str, script: str = "",
                               audience: str = "", platform: str = "youtube",
                               target_length: str = "", style: str = "") -> str:
        sid = _uuid()
        self.db.execute(
            """INSERT INTO planner_sessions (id, project_id, brief, script, audience,
               platform, target_length, style, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?);""",
            (sid, project_id, brief, script, audience, platform, target_length,
             style, "pending", _now()),
        )
        return sid

    def update_planner_session(self, session_id: str, *, status: str,
                               plan_json: str | dict | None = None) -> None:
        if isinstance(plan_json, (dict, list)):
            plan_json = json.dumps(plan_json)
        sets = ["status = ?"]
        params: list[Any] = [status]
        if plan_json is not None:
            sets.append("plan_json = ?")
            params.append(plan_json)
        params.append(session_id)
        self.db.execute(
            f"UPDATE planner_sessions SET {', '.join(sets)} WHERE id = ?;", tuple(params))

    def get_planner_session(self, session_id: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM planner_sessions WHERE id = ?;", (session_id,))
        if not row:
            return None
        d = dict(row)
        d["plan"] = json.loads(d["plan_json"]) if d["plan_json"] else None
        return d

    def list_planner_sessions(self, project_id: str) -> list[dict[str, Any]]:
        rows = [dict(r) for r in self.db.query_all(
            "SELECT * FROM planner_sessions WHERE project_id = ? ORDER BY created_at DESC;",
            (project_id,))]
        for r in rows:
            r["plan"] = json.loads(r["plan_json"]) if r["plan_json"] else None
        return rows

    # ---- Timelines ------------------------------------------------------
    def create_timeline(self, *, project_id: str, name: str, fps: float = 30,
                        duration: float = 0, timeline_json: str | dict | None = None,
                        session_id: str | None = None) -> str:
        tid = _uuid()
        if isinstance(timeline_json, (dict, list)):
            timeline_json = json.dumps(timeline_json)
        self.db.execute(
            """INSERT INTO timelines (id, project_id, session_id, name, fps, duration,
               timeline_json, exported, created_at) VALUES (?,?,?,?,?,?,?,?,?);""",
            (tid, project_id, session_id, name, fps, duration,
             timeline_json or "", 0, _now()),
        )
        return tid

    def get_timeline(self, timeline_id: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM timelines WHERE id = ?;", (timeline_id,))
        if not row:
            return None
        d = dict(row)
        d["timeline"] = json.loads(d["timeline_json"]) if d["timeline_json"] else None
        d["clips"] = self.list_timeline_clips(timeline_id)
        return d

    def list_timelines(self, project_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM timelines WHERE project_id = ? ORDER BY created_at DESC;",
            (project_id,))]

    def add_timeline_clip(self, *, timeline_id: str, video_id: str, track: str,
                          source_start: float, source_end: float,
                          timeline_start: float, timeline_end: float,
                          order_index: int, clip_type: str = "video",
                          transition: str = "hard_cut", label: str = "") -> str:
        cid = _uuid()
        self.db.execute(
            """INSERT INTO timeline_clips (id, timeline_id, video_id, track, source_start,
               source_end, timeline_start, timeline_end, order_index, clip_type,
               transition, label) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);""",
            (cid, timeline_id, video_id, track, source_start, source_end,
             timeline_start, timeline_end, order_index, clip_type, transition, label),
        )
        return cid

    def list_timeline_clips(self, timeline_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM timeline_clips WHERE timeline_id = ? ORDER BY order_index;",
            (timeline_id,))]

    def mark_timeline_exported(self, timeline_id: str) -> None:
        self.db.execute("UPDATE timelines SET exported = 1 WHERE id = ?;", (timeline_id,))

    # ---- Search history -------------------------------------------------
    def add_search_history(self, *, project_id: str, query: str, result_count: int) -> str:
        sid = _uuid()
        self.db.execute(
            "INSERT INTO search_history (id, project_id, query, result_count, created_at) VALUES (?,?,?,?,?);",
            (sid, project_id, query, result_count, _now()),
        )
        return sid

    # ---- Settings -------------------------------------------------------
    def set_setting(self, key: str, value: str) -> None:
        self.db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value;",
            (key, value),
        )

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.db.query_one("SELECT value FROM settings WHERE key = ?;", (key,))
        return row["value"] if row else default

    def get_all_settings(self) -> dict[str, str]:
        return {r["key"]: r["value"] for r in self.db.query_all("SELECT * FROM settings;")}
