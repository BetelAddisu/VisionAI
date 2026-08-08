/* VisionAI frontend — single-file SPA, no build step. */
(() => {
  "use strict";

  const state = {
    view: "dashboard",
    project: null,        // selected project object
    projects: [],
    videos: [],
    jobs: [],
    pollTimer: null,
  };

  const view = document.getElementById("view");
  const viewTitle = document.getElementById("view-title");
  const activeProjectEl = document.getElementById("active-project");
  const statusBar = document.getElementById("status-bar");

  // ---- helpers ----
  const h = (tag, props = {}, ...children) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k === "class") el.className = v;
      else if (k === "html") el.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function")
        el.addEventListener(k.slice(2).toLowerCase(), v);
      else if (k === "attrs") for (const [a, av] of Object.entries(v)) el.setAttribute(a, av);
      else el[k] = v;
    }
    for (const c of children) {
      if (c == null) continue;
      el.append(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return el;
  };

  const fmtTime = (s) => {
    if (!s || s < 0) return "0:00";
    const m = Math.floor(s / 60), sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };
  const fmtDur = (s) => {
    if (!s) return "—";
    const hr = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = Math.floor(s % 60);
    return hr ? `${hr}h ${m}m` : m ? `${m}m ${sec}s` : `${sec}s`;
  };
  const fmtSize = (b) => {
    if (!b) return "—";
    const u = ["B", "KB", "MB", "GB"];
    let i = 0; let n = b;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return `${n.toFixed(1)} ${u[i]}`;
  };

  const toast = (msg, type = "") => {
    const t = h("div", { class: `toast ${type}` }, msg);
    document.body.append(t);
    setTimeout(() => t.remove(), 3500);
  };

  const badge = (text, type) => h("span", { class: `badge badge-${type}` }, text);
  const stageBadge = (status) => {
    const map = {
      completed: ["green", "✓ done"], running: ["blue", "running"],
      failed: ["red", "✗ failed"], pending: ["gray", "pending"],
      skipped: ["gray", "skipped"], queued: ["amber", "queued"],
    };
    const [type, label] = map[status] || ["gray", status];
    return badge(label, type);
  };

  const empty = (icon, msg) =>
    h("div", { class: "empty" },
      h("div", { class: "empty-icon" }, icon),
      h("div", {}, msg));

  // ---- navigation ----
  document.querySelectorAll(".nav-item").forEach(btn =>
    btn.addEventListener("click", () => navigate(btn.dataset.view)));

  function navigate(v) {
    state.view = v;
    document.querySelectorAll(".nav-item").forEach(b =>
      b.classList.toggle("active", b.dataset.view === v));
    const titles = {
      dashboard: "Dashboard", projects: "Projects", media: "Media Library",
      search: "Search Footage", planner: "AI Planner", timeline: "Timeline",
      export: "Export", settings: "Settings",
    };
    viewTitle.textContent = titles[v] || v;
    render();
  }

  function requireProject() {
    if (!state.project) {
      view.append(empty("📂", "Select or create a project first."));
      return false;
    }
    return true;
  }

  async function refreshProjects() {
    try { state.projects = await API.listProjects(); } catch (e) { state.projects = []; }
    updateActiveProject();
  }

  function updateActiveProject() {
    if (state.project) {
      activeProjectEl.innerHTML =
        `<strong>Active project</strong>${escapeHtml(state.project.name)}`;
    } else {
      activeProjectEl.innerHTML = `<strong>No project selected</strong>Choose one in Projects`;
    }
  }

  const escapeHtml = (s) =>
    (s || "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);

  // ---- render dispatcher ----
  async function render() {
    view.innerHTML = "";
    stopPolling();
    try {
      switch (state.view) {
        case "dashboard": await renderDashboard(); break;
        case "projects": await renderProjects(); break;
        case "media": await renderMedia(); break;
        case "search": renderSearch(); break;
        case "planner": await renderPlanner(); break;
        case "timeline": await renderTimeline(); break;
        case "export": await renderExport(); break;
        case "settings": await renderSettings(); break;
      }
    } catch (e) {
      view.append(h("div", { class: "card" },
        h("div", { class: "badge badge-red", style: "margin-bottom:8px" }, "error"),
        h("div", {}, e.message || String(e))));
    }
  }

  // ---- DASHBOARD ----
  async function renderDashboard() {
    if (!requireProject()) return;
    const pid = state.project.id;
    let videoCount = 0, analyzed = 0, jobs = [];
    try {
      state.videos = await API.listVideos(pid);
      videoCount = state.videos.length;
      analyzed = state.videos.filter(v => v.analyzed).length;
      jobs = await API.listJobs(pid);
    } catch (e) { /* ignore */ }

    const running = jobs.filter(j => j.status === "running" || j.status === "pending");
    const recentJobs = jobs.slice(0, 5);

    view.append(
      h("div", { class: "grid grid-4 mb-16" },
        statCard(videoCount, "Videos indexed"),
        statCard(analyzed, "Fully analyzed"),
        statCard(jobs.length, "Total jobs"),
        statCard(running.length, "Active jobs"),
      ),
      h("div", { class: "card" },
        h("div", { class: "card-title" }, "Workflow"),
        h("div", { class: "muted" },
          "Create project → Index footage → Run analysis → Search → AI plan → Build timeline → Export to DaVinci."),
        h("div", { class: "btn-row mt-16" },
          h("button", { class: "btn btn-sm", onclick: () => navigate("media") }, "Open Media"),
          h("button", { class: "btn btn-sm btn-secondary", onclick: () => navigate("search") }, "Search"),
          h("button", { class: "btn btn-sm btn-secondary", onclick: () => navigate("planner") }, "AI Planner"),
        ),
      ),
      h("div", { class: "card" },
        h("div", { class: "card-title" }, "Recent jobs"),
        recentJobs.length
          ? h("div", { class: "list" }, ...recentJobs.map(jobRow))
          : empty("✓", "No jobs yet. Index your footage to get started."),
      ),
    );
  }

  const statCard = (val, label) =>
    h("div", { class: "card" },
      h("div", { class: "stat" },
        h("div", { class: "stat-value" }, String(val)),
        h("div", { class: "stat-label" }, label)));

  const jobRow = (j) =>
    h("div", { class: "list-row" },
      h("div", {},
        h("div", { class: "primary" }, j.job_type.replace(/_/g, " ")),
        h("div", { class: "secondary" }, j.video_id ? `video ${j.video_id.slice(0, 8)}…` : "project-wide"),
      ),
      h("div", { class: "flex items-center gap-12" },
        stageBadge(j.status),
        j.progress ? h("div", { class: "progress", style: "width:80px" },
          h("div", { class: "progress-fill", style: `width:${Math.round(j.progress * 100)}%` })) : null,
      ),
    );

  // ---- PROJECTS ----
  async function renderProjects() {
    await refreshProjects();
    const form = h("div", { class: "card" },
      h("div", { class: "card-title" }, "Create new project"),
      h("div", { class: "field" },
        h("label", {}, "Project name"),
        h("input", { class: "input", id: "p-name", placeholder: "My YouTube channel" }),
      ),
      h("div", { class: "field" },
        h("label", {}, "Video folder path"),
        h("input", { class: "input", id: "p-folder", placeholder: "/home/user/videos" }),
      ),
      h("button", { class: "btn", onclick: async () => {
        const name = document.getElementById("p-name").value.trim();
        const folder = document.getElementById("p-folder").value.trim();
        if (!name || !folder) return toast("Name and folder are required", "error");
        try {
          const p = await API.createProject(name, folder);
          toast("Project created", "success");
          state.project = p;
          await refreshProjects();
          render();
        } catch (e) { toast(e.message, "error"); }
      } }, "Create project"),
    );

    const list = h("div", { class: "card" },
      h("div", { class: "card-title" }, "Your projects"),
      state.projects.length
        ? h("div", { class: "list" }, ...state.projects.map(p =>
            h("div", { class: "list-row" },
              h("div", {},
                h("div", { class: "primary" }, p.name),
                h("div", { class: "secondary" }, p.folder_path || "—"),
              ),
              h("div", { class: "btn-row" },
                h("button", { class: "btn btn-sm", onclick: () => {
                  state.project = p; updateActiveProject(); navigate("dashboard");
                } }, "Open"),
                h("button", { class: "btn btn-sm btn-danger", onclick: async () => {
                  if (!confirm(`Delete project "${p.name}"? This removes all data.`)) return;
                  try { await API.deleteProject(p.id); toast("Deleted", "success");
                    if (state.project && state.project.id === p.id) state.project = null;
                    await refreshProjects(); render();
                  } catch (e) { toast(e.message, "error"); }
                } }, "Delete"),
              ),
            )))
        : empty("📂", "No projects yet. Create one above."),
    );

    view.append(form, list);
  }

  // ---- MEDIA ----
  async function renderMedia() {
    if (!requireProject()) return;
    const pid = state.project.id;
    view.innerHTML = "";

    view.append(
      h("div", { class: "card" },
        h("div", { class: "flex justify-between items-center" },
          h("div", { class: "card-title", style: "margin:0" }, "Index & analyze footage"),
          h("div", { class: "btn-row" },
            h("button", { class: "btn btn-sm", onclick: () => doIndex(pid) }, "Index footage"),
            h("button", { class: "btn btn-sm btn-secondary", onclick: () => doRunJobs(pid) }, "Run analysis jobs"),
          ),
        ),
        h("div", { class: "muted mt-8" },
          "Indexing scans the folder and registers videos. Analysis jobs extract scenes, transcripts, and embeddings."),
      ),
    );

    const videosCard = h("div", { class: "card" }, h("div", { class: "card-title" }, "Videos"));
    try {
      state.videos = await API.listVideos(pid);
    } catch (e) { state.videos = []; }

    if (!state.videos.length) {
      videosCard.append(empty("🎞", "No videos indexed yet. Click “Index footage”."));
      view.append(videosCard);
      return;
    }

    const grid = h("div", { class: "media-grid" });
    for (const v of state.videos) {
      const thumb = v.thumbnail_path
        ? h("img", { class: "media-thumb", src: API.thumbnailUrl(pid, v.id) })
        : h("div", { class: "media-thumb placeholder" }, "no thumbnail");
      grid.append(
        h("div", { class: "media-card", onclick: () => showVideoDetail(pid, v) },
          thumb,
          h("div", { class: "media-body" },
            h("div", { class: "media-title", title: v.filename }, v.filename),
            h("div", { class: "media-meta" },
              h("span", {}, fmtDur(v.duration)),
              h("span", {}, `${v.width || 0}×${v.height || 0}`),
              v.has_audio ? badge("audio", "green") : null,
              v.available ? badge("available", "blue") : badge("missing", "red"),
            ),
          ),
        ),
      );
    }
    videosCard.append(grid);
    view.append(videosCard);

    // Show jobs if any active.
    try {
      state.jobs = await API.listJobs(pid);
      if (state.jobs.length) {
        view.append(h("div", { class: "card" },
          h("div", { class: "card-title" }, "Jobs"),
          h("div", { class: "list" }, ...state.jobs.map(jobRow)),
        ));
        if (state.jobs.some(j => j.status === "pending" || j.status === "running")) {
          startPolling(() => renderMedia());
        }
      }
    } catch (e) { /* ignore */ }
  }

  async function doIndex(pid) {
    try {
      toast("Indexing…", "");
      await API.indexProject(pid, true);
      toast("Indexing started", "success");
      renderMedia();
    } catch (e) { toast(e.message, "error"); }
  }

  async function doRunJobs(pid) {
    try {
      const r = await API.runJobs(pid);
      toast(`Processed ${r.processed} job(s)`, "success");
      renderMedia();
    } catch (e) { toast(e.message, "error"); }
  }

  function showVideoDetail(pid, v) {
    view.innerHTML = "";
    view.append(
      h("div", { class: "btn-row mb-16" },
        h("button", { class: "btn btn-sm btn-ghost", onclick: () => renderMedia() }, "← Back to media"),
        h("button", { class: "btn btn-sm btn-secondary", onclick: async () => {
          try { toast("Analyzing…", ""); await API.analyzeVideo(pid, v.id);
            toast("Analysis complete", "success"); showVideoDetail(pid, v);
          } catch (e) { toast(e.message, "error"); }
        } }, "Analyze now"),
      ),
      h("div", { class: "card" },
        h("div", { class: "card-title" }, v.filename),
        h("div", { class: "grid grid-3" },
          metaRow("Duration", fmtDur(v.duration)),
          metaRow("Resolution", `${v.width || 0} × ${v.height || 0}`),
          metaRow("FPS", v.fps ? v.fps.toFixed(2) : "—"),
          metaRow("Codec", v.codec || "—"),
          metaRow("Audio", v.has_audio ? v.audio_codec || "yes" : "none"),
          metaRow("Size", fmtSize(v.file_size)),
          metaRow("Category", v.media_category || "raw"),
          metaRow("Hash", v.hash ? v.hash.slice(0, 12) + "…" : "—"),
          metaRow("Available", v.available ? "yes" : "no"),
        ),
      ),
    );
    // Load analysis state + transcript.
    (async () => {
      try {
        const detail = await API.getVideo(pid, v.id);
        if (detail.analysis_state && detail.analysis_state.length) {
          view.append(h("div", { class: "card" },
            h("div", { class: "card-title" }, "Analysis stages"),
            h("div", { class: "stage-list" },
              ...detail.analysis_state.map(s =>
                h("div", { class: "stage-row" },
                  h("span", { class: "stage-name" }, s.stage),
                  stageBadge(s.status),
                ))),
          ));
        }
        if (detail.transcript && detail.transcript.length) {
          view.append(h("div", { class: "card" },
            h("div", { class: "card-title" }, `Transcript (${detail.transcript.length} segments)`),
            ...detail.transcript.map(seg =>
              h("div", { class: "result-snippet" },
                h("span", { class: "result-time" }, `${fmtTime(seg.start_time)} → ${fmtTime(seg.end_time)}`),
                h("div", { class: "mt-8" }, escapeHtml(seg.text)),
              )),
          ));
        }
      } catch (e) { /* ignore */ }
    })();
  }

  const metaRow = (label, value) =>
    h("div", {}, h("div", { class: "stat-label" }, label), h("div", { style: "font-weight:600" }, value));

  // ---- SEARCH ----
  function renderSearch() {
    if (!requireProject()) return;
    const pid = state.project.id;
    const resultsDiv = h("div", { id: "search-results" });

    view.append(
      h("div", { class: "card" },
        h("div", { class: "card-title" }, "Search your footage"),
        h("div", { class: "field" },
          h("label", {}, "Natural-language query"),
          h("input", { class: "input", id: "search-q",
            placeholder: "Find clips where I explain AWS deployment" }),
        ),
        h("div", { class: "grid grid-3" },
          h("div", { class: "field" },
            h("label", {}, "Category"), categorySelect("search-cat")),
          h("div", { class: "field" },
            h("label", {}, "Min duration (s)"),
            h("input", { class: "input", id: "search-min-dur", type: "number", placeholder: "0" })),
          h("div", { class: "field" },
            h("label", {}, "Max results"),
            h("input", { class: "input", id: "search-limit", type: "number", value: "20" })),
        ),
        h("button", { class: "btn", onclick: () => doSearch(pid, resultsDiv) }, "Search"),
        h("div", { class: "muted mt-8" },
          "Search combines transcript keywords, semantic similarity and metadata. Results never invent clips."),
      ),
      resultsDiv,
    );
  }

  const categorySelect = (id) => {
    const sel = h("select", { class: "select", id });
    ["", "raw", "broll", "podcast", "interview", "archive", "audio"].forEach(c =>
      sel.append(h("option", { value: c }, c || "any")));
    return sel;
  };

  async function doSearch(pid, container) {
    const query = document.getElementById("search-q").value.trim();
    if (!query) return toast("Enter a search query", "error");
    const cat = document.getElementById("search-cat").value;
    const minDur = parseFloat(document.getElementById("search-min-dur").value) || null;
    const limit = parseInt(document.getElementById("search-limit").value) || 20;
    container.innerHTML = "";
    container.append(h("div", { class: "muted" }, "Searching…"));
    try {
      const filters = {};
      if (cat) filters.category = cat;
      if (minDur) filters.min_duration = minDur;
      const res = await API.search(pid, query, filters, limit);
      container.innerHTML = "";
      if (!res.results.length) {
        container.append(empty("🔍", "No matching clips found."));
        return;
      }
      container.append(h("div", { class: "muted mb-16" },
        `${res.count} result(s) for “${escapeHtml(res.query)}”`));
      for (const r of res.results) {
        container.append(
          h("div", { class: "search-result" },
            h("div", { class: "result-head" },
              h("div", {},
                h("div", { class: "result-file" }, r.filename || r.video_id.slice(0, 8)),
                h("div", { class: "result-time" },
                  `${fmtTime(r.start_time)} → ${fmtTime(r.end_time)} (${fmtDur(r.end_time - r.start_time)})`),
              ),
              h("div", { style: "text-align:right" },
                badge(`score ${(r.score * 100).toFixed(0)}%`, "green"),
                h("div", { class: "score-bar" },
                  h("div", { class: "score-fill", style: `width:${Math.round(r.score * 100)}%` })),
              ),
            ),
            r.transcript_snippet
              ? h("div", { class: "result-snippet" }, escapeHtml(r.transcript_snippet))
              : null,
            r.reason ? h("div", { class: "result-reason" }, `Why: ${escapeHtml(r.reason)}`) : null,
          ),
        );
      }
    } catch (e) {
      container.innerHTML = "";
      container.append(h("div", { class: "card" }, `Search failed: ${e.message}`));
    }
  }

  // ---- PLANNER ----
  async function renderPlanner() {
    if (!requireProject()) return;
    const pid = state.project.id;

    view.append(
      h("div", { class: "card" },
        h("div", { class: "card-title" }, "Create an editing plan"),
        h("div", { class: "field" },
          h("label", {}, "Brief / story idea"),
          h("textarea", { class: "textarea", id: "pl-brief",
            placeholder: "A 60-second tutorial about deploying an app to AWS cloud" }),
        ),
        h("div", { class: "field" },
          h("label", {}, "Script (optional)"),
          h("textarea", { class: "textarea", id: "pl-script",
            placeholder: "Paste your script here…" }),
        ),
        h("div", { class: "grid grid-3" },
          h("div", { class: "field" },
            h("label", {}, "Platform"),
            platformSelect("pl-platform")),
          h("div", { class: "field" },
            h("label", {}, "Target length"),
            lengthSelect("pl-length")),
          h("div", { class: "field" },
            h("label", {}, "Audience"),
            h("input", { class: "input", id: "pl-audience", placeholder: "developers" })),
        ),
        h("button", { class: "btn", onclick: () => doPlan(pid) }, "Generate plan"),
        h("div", { class: "muted mt-8" },
          "The planner searches your indexed footage and builds a grounded plan. It never invents clips that don’t exist."),
      ),
    );

    // List existing plans.
    try {
      const plans = await API.listPlans(pid);
      if (plans.length) {
        view.append(h("div", { class: "card" },
          h("div", { class: "card-title" }, "Saved plans"),
          h("div", { class: "list" }, ...plans.map(p =>
            h("div", { class: "list-row" },
              h("div", {},
                h("div", { class: "primary" }, p.brief.slice(0, 60) || "Untitled"),
                h("div", { class: "secondary" },
                  `${p.platform} · ${p.status} · ${p.created_at || ""}`),
              ),
              h("button", { class: "btn btn-sm btn-secondary", onclick: () => showPlan(pid, p.id) }, "View"),
            ))),
        ));
      }
    } catch (e) { /* ignore */ }
  }

  const platformSelect = (id) => {
    const sel = h("select", { class: "select", id });
    ["youtube", "tiktok", "instagram", "shorts", "podcast"].forEach(p =>
      sel.append(h("option", { value: p }, p)));
    return sel;
  };
  const lengthSelect = (id) => {
    const sel = h("select", { class: "select", id });
    ["", "short", "medium", "long"].forEach(l =>
      sel.append(h("option", { value: l }, l || "auto")));
    return sel;
  };

  async function doPlan(pid) {
    const brief = document.getElementById("pl-brief").value.trim();
    if (!brief) return toast("Enter a brief", "error");
    const body = {
      brief,
      script: document.getElementById("pl-script").value.trim(),
      platform: document.getElementById("pl-platform").value,
      target_length: document.getElementById("pl-length").value,
      audience: document.getElementById("pl-audience").value.trim(),
    };
    toast("Generating plan…", "");
    try {
      const res = await API.createPlan(pid, body);
      toast("Plan generated", "success");
      showPlan(pid, res.session_id, res.plan);
    } catch (e) { toast(e.message, "error"); }
  }

  async function showPlan(pid, sessionId, plan) {
    if (!plan) {
      try { const s = await API.getPlan(pid, sessionId); plan = s.plan; }
      catch (e) { return toast(e.message, "error"); }
    }
    view.innerHTML = "";
    view.append(
      h("div", { class: "btn-row mb-16" },
        h("button", { class: "btn btn-sm btn-ghost", onclick: () => renderPlanner() }, "← Back to planner"),
        h("button", { class: "btn btn-sm", onclick: () => {
          state._pendingSession = sessionId;
          state._pendingPlan = plan;
          navigate("timeline");
        } }, "Build timeline →"),
      ),
      h("div", { class: "card" },
        h("div", { class: "card-title" }, plan.title || "Editing plan"),
        h("div", { class: "grid grid-3 mb-16" },
          metaRow("Platform", plan.platform),
          metaRow("Length", plan.target_length || "auto"),
          metaRow("Sections", String(plan.sections?.length || 0)),
        ),
        plan.unresolved && plan.unresolved.length
          ? h("div", { class: "badge badge-amber", style: "margin-bottom:10px" },
              `${plan.unresolved.length} unresolved requirement(s)`)
          : null,
      ),
    );

    if (plan.sections) {
      const card = h("div", { class: "card" }, h("div", { class: "card-title" }, "Story structure"));
      for (const s of plan.sections) {
        card.append(
          h("div", { class: "plan-section" },
            h("div", { class: "sec-type" }, s.type),
            h("div", { class: "sec-label" }, s.label || s.type),
            s.target_duration ? h("div", { class: "muted" },
              `~ ${fmtDur(s.target_duration)} at ${fmtTime(s.target_start)}`) : null,
            s.clips && s.clips.length
              ? h("div", { class: "plan-clips" }, ...s.clips.map(c =>
                  h("div", { class: "plan-clip" },
                    `${c.filename || "clip"} · ${fmtTime(c.source_start)}→${fmtTime(c.source_end)}`)))
              : h("div", { class: "plan-clip muted" }, "no clip (unresolved)"),
          ),
        );
      }
      view.append(card);
    }

    if (plan.recommendations && plan.recommendations.length) {
      const recs = h("div", { class: "card" }, h("div", { class: "card-title" }, "Recommendations"));
      for (const r of plan.recommendations) {
        recs.append(h("div", { class: "result-snippet" }, escapeHtml(r)));
      }
      view.append(recs);
    }

    const colorRec = plan.color_recommendation;
    const musicRec = plan.music_recommendation;
    if ((colorRec && Object.keys(colorRec).length) || (musicRec && Object.keys(musicRec).length)) {
      view.append(h("div", { class: "card" },
        h("div", { class: "card-title" }, "Color & audio direction"),
        colorRec && colorRec.recommendation
          ? h("div", { class: "mb-8" }, h("strong", {}, "Color: "), escapeHtml(colorRec.recommendation))
          : null,
        musicRec
          ? h("div", {}, h("strong", {}, "Music: "),
              escapeHtml(`${musicRec.music_style || ""} · ${musicRec.energy || ""} · ${musicRec.ducking || ""}`))
          : null,
      ));
    }
  }

  // ---- TIMELINE ----
  async function renderTimeline() {
    if (!requireProject()) return;
    const pid = state.project.id;

    // If coming from planner with a pending session.
    if (state._pendingSession) {
      const sid = state._pendingSession;
      state._pendingSession = null;
      view.append(
        h("div", { class: "card" },
          h("div", { class: "card-title" }, "Build timeline from plan"),
          h("div", { class: "field" },
            h("label", {}, "Timeline name"),
            h("input", { class: "input", id: "tl-name", value: `Draft ${new Date().toLocaleDateString()}` })),
          h("button", { class: "btn", onclick: async () => {
            try {
              const name = document.getElementById("tl-name").value.trim();
              const r = await API.buildTimeline(pid, sid, name);
              toast("Timeline built", "success");
              showTimeline(pid, r.timeline_id, r.timeline);
            } catch (e) { toast(e.message, "error"); }
          } }, "Build timeline"),
        ),
      );
      return;
    }

    try {
      const timelines = await API.listTimelines(pid);
      view.append(h("div", { class: "card" },
        h("div", { class: "card-title" }, "Timelines"),
        timelines.length
          ? h("div", { class: "list" }, ...timelines.map(t =>
              h("div", { class: "list-row" },
                h("div", {},
                  h("div", { class: "primary" }, t.name),
                  h("div", { class: "secondary" },
                    `${fmtDur(t.duration)} · ${t.exported ? "exported" : "not exported"}`)),
                h("button", { class: "btn btn-sm btn-secondary", onclick: () => showTimeline(pid, t.id) }, "View"),
              )))
          : empty("🗂", "No timelines yet. Generate a plan first, then build a timeline."),
      ));
    } catch (e) { view.append(h("div", { class: "card" }, e.message)); }
  }

  async function showTimeline(pid, tid, preloaded) {
    let tl = preloaded;
    if (!tl) {
      try { tl = await API.getTimeline(pid, tid); }
      catch (e) { return toast(e.message, "error"); }
    }
    view.innerHTML = "";
    const tlJson = tl.timeline || tl || { clips: [] };
    const clips = tlJson.clips || tl.clips || [];
    const duration = tl.duration || tlJson.duration || 0;

    view.append(
      h("div", { class: "btn-row mb-16" },
        h("button", { class: "btn btn-sm btn-ghost", onclick: () => renderTimeline() }, "← Back"),
        h("button", { class: "btn btn-sm", onclick: () => {
          state._lastTimeline = tl; navigate("export");
        } }, "Export →"),
      ),
      h("div", { class: "card" },
        h("div", { class: "flex justify-between items-center" },
          h("div", { class: "card-title", style: "margin:0" }, tl.name),
          badge(`${clips.length} clips`, "blue"),
        ),
        h("div", { class: "muted mt-8" }, `Duration: ${fmtDur(duration)} · ${tl.fps || 30} fps`),
      ),
    );

    if (clips.length) {
      const tracksCard = h("div", { class: "card" }, h("div", { class: "card-title" }, "Track layout"));
      const tracksEl = h("div", { class: "timeline-tracks" });
      const tracks = [...new Set(clips.map(c => c.track))].sort();
      for (const track of tracks) {
        const trackClips = h("div", { class: "track-clips" });
        for (const c of clips.filter(c => c.track === track)) {
          const left = duration ? (c.timeline_start / duration) * 100 : 0;
          const width = duration ? ((c.timeline_end - c.timeline_start) / duration) * 100 : 10;
          trackClips.append(h("div", { class: "clip-block",
            style: `left:${left}%;width:${Math.max(width, 3)}%`,
            title: `${c.filename || ""} ${fmtTime(c.source_start)}→${fmtTime(c.source_end)}` },
            c.label || c.filename || "clip"));
        }
        tracksEl.append(h("div", { class: "track" },
          h("div", { class: "track-label" }, track), trackClips));
      }
      tracksCard.append(tracksEl);
      view.append(tracksCard);

      // Clip list.
      view.append(h("div", { class: "card" },
        h("div", { class: "card-title" }, "Clips"),
        h("div", { class: "list" }, ...clips.map((c, i) =>
          h("div", { class: "list-row" },
            h("div", {},
              h("div", { class: "primary" }, `${i + 1}. ${c.filename || c.video_id.slice(0, 8)}`),
              h("div", { class: "secondary" },
                `${c.track} · source ${fmtTime(c.source_start)}→${fmtTime(c.source_end)} → timeline ${fmtTime(c.timeline_start)}`),
            ),
            badge(c.clip_type || "video", "gray"),
          ))),
      ));
    }
  }

  // ---- EXPORT ----
  async function renderExport() {
    if (!requireProject()) return;
    const pid = state.project.id;
    let timelines = [];
    try { timelines = await API.listTimelines(pid); } catch (e) {}

    view.append(
      h("div", { class: "card" },
        h("div", { class: "card-title" }, "Export to DaVinci Resolve"),
        h("div", { class: "muted mb-16" },
          "Exports a DaVinci-compatible XML timeline and optional SRT subtitles. Open the XML in Resolve to finish color, audio and effects."),
      ),
    );

    if (!timelines.length) {
      view.append(h("div", { class: "card" }, empty("🗂", "No timelines to export. Build one first.")));
      return;
    }

    view.append(h("div", { class: "card" },
      h("div", { class: "card-title" }, "Timelines"),
      h("div", { class: "list" }, ...timelines.map(t =>
        h("div", { class: "list-row" },
          h("div", {},
            h("div", { class: "primary" }, t.name),
            h("div", { class: "secondary" },
              `${fmtDur(t.duration)} · ${t.exported ? badge("exported", "green") : badge("not exported", "gray")}`)),
          h("div", { class: "btn-row" },
            h("button", { class: "btn btn-sm", onclick: () => doExport(pid, t.id) }, "Export XML"),
            h("button", { class: "btn btn-sm btn-secondary", onclick: () => doExportSrt(pid, t.id) }, "Export SRT"),
          ),
        ))),
    ));
  }

  async function doExport(pid, tid) {
    try {
      const r = await API.exportTimeline(pid, tid);
      toast(`XML exported: ${r.xml}`, "success");
    } catch (e) { toast(e.message, "error"); }
  }
  async function doExportSrt(pid, tid) {
    try {
      const r = await API.exportSrt(pid, tid);
      toast(r.srt ? `SRT exported: ${r.srt}` : "No subtitles to export", r.srt ? "success" : "");
    } catch (e) { toast(e.message, "error"); }
  }

  // ---- SETTINGS ----
  async function renderSettings() {
    let appCfg = {};
    try { appCfg = await API.appSettings(); } catch (e) {}

    view.append(
      h("div", { class: "card" },
        h("div", { class: "card-title" }, "Application configuration"),
        h("div", { class: "muted mb-16" },
          "These reflect the loaded config/default.yaml. AI providers default to local/offline; no cloud key is required."),
        h("div", { class: "grid grid-2" },
          cfgRow("App", appCfg.app),
          cfgRow("Indexing", appCfg.indexing),
          cfgRow("Pipeline", appCfg.pipeline),
          cfgRow("Proxy", appCfg.proxy),
        ),
      ),
    );

    if (state.project) {
      let settings = {};
      try { settings = await API.projectSettings(state.project.id); } catch (e) {}
      const card = h("div", { class: "card" },
        h("div", { class: "card-title" }, `Project settings — ${state.project.name}`),
      );
      const entries = Object.entries(settings);
      if (entries.length) {
        const list = h("div", { class: "list" });
        for (const [k, v] of entries) {
          list.append(h("div", { class: "list-row" },
            h("div", { class: "primary" }, k),
            h("div", { class: "secondary" }, String(v)),
          ));
        }
        card.append(list);
      } else {
        card.append(h("div", { class: "muted" }, "No project-specific settings set."));
      }
      view.append(card);
    }
  }

  const cfgRow = (title, obj) => {
    if (!obj) return h("div", {});
    const items = Object.entries(obj).map(([k, v]) =>
      h("div", { class: "stage-row" },
        h("span", { class: "stage-name" }, k),
        h("span", { class: "dim" }, typeof v === "object" ? JSON.stringify(v) : String(v)),
      ));
    return h("div", {},
      h("div", { class: "card-title", style: "font-size:12px;text-transform:uppercase;color:var(--text-muted)" }, title),
      ...items);
  };

  // ---- polling ----
  function startPolling(cb) {
    stopPolling();
    state.pollTimer = setInterval(cb, 4000);
  }
  function stopPolling() {
    if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = null; }
  }

  // ---- init ----
  (async () => {
    try {
      const h = await API.health();
      statusBar.textContent = `● online · v${h.version}`;
    } catch (e) {
      statusBar.textContent = "● offline";
    }
    await refreshProjects();
    navigate("dashboard");
  })();
})();
