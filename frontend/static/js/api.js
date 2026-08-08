/* API client for the VisionAI backend. All calls go to /api. */
const API = (() => {
  const base = "/api";

  async function req(path, options = {}) {
    const opts = {
      headers: { "Content-Type": "application/json" },
      ...options,
    };
    if (opts.body && typeof opts.body !== "string") {
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(base + path, opts);
    if (!res.ok) {
      let detail = res.statusText;
      try { const j = await res.json(); detail = j.detail || detail; } catch (e) {}
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  return {
    // Health
    health: () => fetch("/health").then(r => r.json()),

    // Projects
    listProjects: () => req("/projects"),
    getProject: (id) => req(`/projects/${id}`),
    createProject: (name, folder_path) =>
      req("/projects", { method: "POST", body: { name, folder_path } }),
    deleteProject: (id) => req(`/projects/${id}`, { method: "DELETE" }),
    indexProject: (id, run_async = true) =>
      req(`/projects/${id}/index?run_async=${run_async}`, { method: "POST" }),

    // Videos
    listVideos: (pid) => req(`/projects/${pid}/videos`),
    getVideo: (pid, vid) => req(`/projects/${pid}/videos/${vid}`),
    analyzeVideo: (pid, vid, force = false) =>
      req(`/projects/${pid}/videos/${vid}/analyze?force=${force}`, { method: "POST" }),
    getTranscript: (pid, vid) => req(`/projects/${pid}/videos/${vid}/transcript`),
    getScenes: (pid, vid) => req(`/projects/${pid}/videos/${vid}/scenes`),
    thumbnailUrl: (pid, vid) => `/api/projects/${pid}/videos/${vid}/thumbnail`,

    // Jobs
    listJobs: (pid, status) =>
      req(`/projects/${pid}/jobs${status ? `?status=${status}` : ""}`),
    getJob: (pid, jid) => req(`/projects/${pid}/jobs/${jid}`),
    runJobs: (pid) => req(`/projects/${pid}/jobs/run`, { method: "POST" }),
    cancelJob: (pid, jid) => req(`/projects/${pid}/jobs/${jid}/cancel`, { method: "POST" }),

    // Search
    search: (pid, query, filters = {}, limit = 20) =>
      req(`/projects/${pid}/search`, { method: "POST", body: { query, limit, ...filters } }),

    // Planner
    createPlan: (pid, body) => req(`/projects/${pid}/plan`, { method: "POST", body }),
    listPlans: (pid) => req(`/projects/${pid}/plans`),
    getPlan: (pid, sid) => req(`/projects/${pid}/plans/${sid}`),

    // Timeline
    buildTimeline: (pid, session_id, name) =>
      req(`/projects/${pid}/timelines`, { method: "POST", body: { session_id, name } }),
    listTimelines: (pid) => req(`/projects/${pid}/timelines`),
    getTimeline: (pid, tid) => req(`/projects/${pid}/timelines/${tid}`),
    exportTimeline: (pid, tid, version = 1) =>
      req(`/projects/${pid}/timelines/${tid}/export?version=${version}`, { method: "POST" }),
    exportSrt: (pid, tid) =>
      req(`/projects/${pid}/timelines/${tid}/export-srt`, { method: "POST" }),

    // Settings
    appSettings: () => req("/settings/app"),
    projectSettings: (pid) => req(`/projects/${pid}/settings`),
    setSetting: (pid, key, value) =>
      req(`/projects/${pid}/settings`, { method: "PUT", body: { key, value } }),
  };
})();
