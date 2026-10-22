/*
 * SpecPilot voice input for agent.html
 *
 * Flow (same endpoints as audio_test.html):
 *   1. Click mic  -> records
 *   2. Click again -> POST /audio/transcribe/{project_id}
 *   3. Text appears in your chat input so the user can fix it
 *   4. "Approve & send" -> PUT /audio/transcripts/{pid}/{tid}  (approve: true)
 *                       -> POST /audio/transcripts/{pid}/{tid}/submit
 *   5. Your onReply(result) callback receives the agent's answer
 */
(function (global) {
  "use strict";

  var CSS = [
    ".sp-mic svg{width:22px;height:22px;fill:currentColor;pointer-events:none;}",
    ".sp-mic.sp-plain{width:48px;height:48px;flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;",
    "border:0;border-radius:50%;background:#4338ca;color:#fff;cursor:pointer;padding:0;}",
    ".sp-mic:focus-visible{outline:2px solid #4338ca;outline-offset:2px;}",
    ".sp-mic.sp-rec{background:#b3261e !important;border-color:#b3261e !important;color:#fff !important;}",
    ".sp-mic.sp-busy{opacity:.5;cursor:wait;}",
    ".sp-mic:disabled{cursor:not-allowed;}",
    "@media (prefers-reduced-motion:no-preference){.sp-mic.sp-rec{animation:sp-pulse 1.1s infinite;}}",
    "@keyframes sp-pulse{50%{box-shadow:0 0 0 6px rgba(179,38,30,.25);}}",
    ".sp-timer{display:none;align-self:center;padding:3px 10px;border-radius:99px;background:#fbe9e7;color:#b3261e;",
    "font:600 14px/1.3 system-ui,-apple-system,'Segoe UI',sans-serif;font-variant-numeric:tabular-nums;white-space:nowrap;}",
    ".sp-timer.sp-show{display:inline-block;}",
    ".sp-bar{display:none;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 12px;margin:0 0 8px;",
    "border:1px solid #cfd7df;border-left:3px solid #4338ca;border-radius:4px;background:#f6f8fa;",
    "font:14px/1.4 system-ui,-apple-system,'Segoe UI',sans-serif;color:#1c2530;}",
    ".sp-bar.sp-show{display:flex;}",
    ".sp-bar .sp-text{flex:1 1 220px;}",
    ".sp-bar.sp-err{border-left-color:#b3261e;color:#b3261e;}",
    ".sp-bar button{font:inherit;padding:6px 12px;border-radius:4px;border:1px solid #cfd7df;background:#fff;color:#1c2530;cursor:pointer;}",
    ".sp-bar button.sp-go{background:#4338ca;border-color:#4338ca;color:#fff;}",
    ".sp-bar button:disabled{opacity:.5;cursor:not-allowed;}"
  ].join("");

  var MIC_SVG =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z"/></svg>';

  function init(userCfg) {
    var cfg = Object.assign({
      apiBase: "http://127.0.0.1:8000",
      inputSelector: "#messageInput",   // your chat textbox
      sendButtonSelector: null,          // mic is placed before this button (auto-detected if null)
      fileInputSelector: "#documentUploadInput", // your attach-file input; audio files picked here go to transcription
      containerSelector: null,           // the rounded pill that holds the input (review bar goes above it)
      useMaterialIcon: true,             // use the Material Symbols "mic" icon (your page already loads it)
      matchSendButtonStyle: true,        // copy the send button's CSS classes so the mic matches
      getToken: function () {
        return localStorage.getItem("access_token") ||
               localStorage.getItem("token") ||
               sessionStorage.getItem("access_token") ||
               sessionStorage.getItem("token") || "";
      },
      getProjectId: function () {
        var q = new URLSearchParams(location.search);
        return q.get("project_id") || q.get("id") || localStorage.getItem("project_id");
      },
      getThreadId: function () {
        // Use the SAME thread id your text chat uses, so voice and typed messages share one conversation
        return localStorage.getItem("thread_id") || ("voice-" + Date.now());
      },
      onReply: null,   // function (result) { ...render agent_response in your chat... }
      onError: null    // optional
    }, userCfg || {});

    var input = document.querySelector(cfg.inputSelector);
    if (!input) { console.error("[SpecPilotMic] input not found:", cfg.inputSelector); return; }

    // ---- styles ----
    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    // ---- mic button ----
    var mic = document.createElement("button");
    mic.type = "button";
    mic.title = "Record a voice note";
    mic.setAttribute("aria-label", "Record a voice note");
    function setIcon(name) {
      if (cfg.useMaterialIcon) mic.innerHTML = '<span class="material-symbols-outlined">' + name + '</span>';
      else mic.innerHTML = MIC_SVG;
    }
    setIcon("mic");

    // Find the send button: use the selector if given, otherwise the first <button> near the input
    var sendBtn = cfg.sendButtonSelector ? document.querySelector(cfg.sendButtonSelector) : null;
    if (!sendBtn) {
      var node = input.parentElement;
      for (var depth = 0; node && depth < 4 && !sendBtn; depth++, node = node.parentElement) {
        sendBtn = node.querySelector("button");
      }
    }

    // Look like your existing round buttons (copies the send button's classes), else use built-in style
    if (sendBtn && sendBtn.className && cfg.matchSendButtonStyle) mic.className = "sp-mic " + sendBtn.className;
    else mic.className = "sp-mic sp-plain";

    if (sendBtn && sendBtn.parentNode) sendBtn.parentNode.insertBefore(mic, sendBtn);
    else input.insertAdjacentElement("afterend", mic);

    // live recording timer shown right beside the mic
    var chip = document.createElement("span");
    chip.className = "sp-timer";
    chip.textContent = "0:00";
    mic.parentNode.insertBefore(chip, mic);

    // ---- review bar: placed above the whole pill (the closest ancestor holding both input and mic) ----
    var bar = document.createElement("div");
    bar.className = "sp-bar";
    bar.setAttribute("role", "status");
    var barText = document.createElement("span");
    barText.className = "sp-text";
    var goBtn = document.createElement("button");
    goBtn.type = "button"; goBtn.className = "sp-go"; goBtn.textContent = "Approve & send"; goBtn.hidden = true;
    var cancelBtn = document.createElement("button");
    cancelBtn.type = "button"; cancelBtn.textContent = "Discard"; cancelBtn.hidden = true;
    bar.appendChild(barText); bar.appendChild(goBtn); bar.appendChild(cancelBtn);

    var pill = cfg.containerSelector ? document.querySelector(cfg.containerSelector) : null;
    if (!pill) {
      pill = input.parentElement;
      while (pill && !pill.contains(mic)) pill = pill.parentElement;
      // go one level up if the common parent is just a tiny wrapper
      if (pill && pill.parentElement && pill.children.length < 3) pill = pill.parentElement;
    }
    pill.parentNode.insertBefore(bar, pill);

    // ---- state ----
    var recorder = null, chunks = [], stream = null, timer = null, startedAt = 0;
    var transcriptId = null;

    function say(text, opts) {
      opts = opts || {};
      bar.className = "sp-bar sp-show" + (opts.error ? " sp-err" : "");
      barText.textContent = text;
      goBtn.hidden = !opts.review;
      cancelBtn.hidden = !opts.review;
    }
    function hideBar() { bar.className = "sp-bar"; }
    function fail(msg) {
      say(msg, { error: true });
      if (cfg.onError) cfg.onError(msg);
    }
    function fmt(ms) {
      var s = Math.floor(ms / 1000);
      return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
    }

    async function api(method, path, opts) {
      opts = opts || {};
      var headers = {};
      var token = cfg.getToken();
      if (token) headers["Authorization"] = "Bearer " + token;
      var init = { method: method, headers: headers };
      if (opts.json) { headers["Content-Type"] = "application/json"; init.body = JSON.stringify(opts.json); }
      if (opts.form) init.body = opts.form;
      var res, data = null;
      try { res = await fetch(cfg.apiBase.replace(/\/+$/, "") + path, init); }
      catch (e) { throw new Error("Cannot reach the server. Check that the backend is running and CORS allows this page."); }
      try { data = await res.json(); } catch (e) {}
      if (!res.ok) {
        var d = data && data.detail;
        var err = new Error(d ? (typeof d === "string" ? d : JSON.stringify(d)) : "Request failed (" + res.status + ")");
        err.status = res.status;
        throw err;
      }
      return data;
    }

    function pid() {
      var p = cfg.getProjectId();
      if (!p) throw new Error("No project selected. Open a project first.");
      return encodeURIComponent(p);
    }

    // ---- recording ----
    function pickMime() {
      var types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
      for (var i = 0; i < types.length; i++) {
        if (global.MediaRecorder && MediaRecorder.isTypeSupported(types[i])) return types[i];
      }
      return "";
    }

    async function startRecording() {
      if (!navigator.mediaDevices || !global.MediaRecorder) {
        fail("This browser can't record audio."); return;
      }
      try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
      catch (e) { fail("Microphone blocked. Allow it in the address bar and try again."); return; }

      var mime = pickMime();
      chunks = [];
      recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      recorder.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
      recorder.onstop = onStopped;
      recorder.start();

      startedAt = Date.now();
      mic.classList.add("sp-rec");
      setIcon("stop");
      mic.title = "Stop recording";
      mic.setAttribute("aria-label", "Stop recording");
      chip.textContent = "0:00";
      chip.classList.add("sp-show");
      say("Recording 0:00. Click the mic again to stop.");
      timer = setInterval(function () {
        var t = fmt(Date.now() - startedAt);
        chip.textContent = t;
        say("Recording " + t + ". Click the mic again to stop.");
      }, 250);
    }

    function stopRecording() {
      if (recorder && recorder.state === "recording") recorder.stop();
    }

    async function onStopped() {
      clearInterval(timer);
      var secs = Math.max(1, Math.round((Date.now() - startedAt) / 1000));
      chip.classList.remove("sp-show");
      stream.getTracks().forEach(function (t) { t.stop(); });
      mic.classList.remove("sp-rec");
      setIcon("mic");
      mic.title = "Record a voice note";
      mic.setAttribute("aria-label", "Record a voice note");

      var type = recorder.mimeType || "audio/webm";
      var blob = new Blob(chunks, { type: type });
      if (!blob.size) { fail("Nothing was recorded. Try again."); return; }
      var ext = type.indexOf("mp4") !== -1 ? "m4a" : "webm";
      await transcribe(blob, "recording." + ext, secs);
    }

    // ---- transcribe ----
    async function transcribe(blob, name, secs) {
      mic.disabled = true; mic.classList.add("sp-busy");
      say(secs ? "Recorded " + secs + " seconds. Transcribing..." : "Transcribing " + name + "...");
      try {
        var fd = new FormData();
        fd.append("file", blob, name);
        var t = await api("POST", "/audio/transcribe/" + pid(), { form: fd });
        if (t.status === "failed") throw new Error(t.error_message || "Transcription failed.");
        transcriptId = t.id;
        input.value = t.edited_text || t.raw_text || "";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
        say("Check the text below, fix anything that's wrong, then approve.", { review: true });
      } catch (e) {
        fail(e.message + (e.status === 401 ? " Please log in again." : ""));
      } finally {
        mic.disabled = false; mic.classList.remove("sp-busy");
      }
    }

    // ---- approve + submit ----
    goBtn.onclick = async function () {
      if (!transcriptId) return;
      var text = input.value.trim();
      if (!text) { fail("The text is empty."); return; }
      goBtn.disabled = cancelBtn.disabled = true;
      say("Sending to the requirement agent...");
      try {
        await api("PUT", "/audio/transcripts/" + pid() + "/" + transcriptId, {
          json: { edited_text: text, approve: true }
        });
        var r = await api("POST", "/audio/transcripts/" + pid() + "/" + transcriptId + "/submit", {
          json: { thread_id: cfg.getThreadId() }
        });
        transcriptId = null;
        input.value = "";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        hideBar();
        var detail = { userText: text, result: r };
        document.dispatchEvent(new CustomEvent("specpilot:audio-reply", { detail: detail }));
        if (cfg.onReply) cfg.onReply(r, text);
      } catch (e) {
        fail(e.message);
        goBtn.hidden = false; cancelBtn.hidden = false;
      } finally {
        goBtn.disabled = cancelBtn.disabled = false;
      }
    };

    cancelBtn.onclick = function () {
      transcriptId = null;
      input.value = "";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      hideBar();
    };

    // ---- attach button: accept audio files and send them to transcription ----
    var fileInput = document.querySelector(cfg.fileInputSelector);
    if (fileInput) {
      var AUDIO_EXT = /\.(mp3|wav|m4a|webm)$/i;
      var acc = (fileInput.getAttribute("accept") || "").split(",").map(function (x) { return x.trim(); }).filter(Boolean);
      [".mp3", ".wav", ".m4a", ".webm"].forEach(function (x) { if (acc.indexOf(x) === -1) acc.push(x); });
      fileInput.setAttribute("accept", acc.join(","));

      // capture phase on document: runs before your existing upload handler
      document.addEventListener("change", function (e) {
        if (e.target !== fileInput) return;
        var f = fileInput.files && fileInput.files[0];
        if (!f) return;
        var isAudio = AUDIO_EXT.test(f.name) || (f.type && f.type.indexOf("audio/") === 0);
        if (!isAudio) return;               // documents continue to your normal upload code
        e.stopImmediatePropagation();
        fileInput.value = "";
        try { pid(); } catch (err) { fail(err.message); return; }
        transcribe(f, f.name);
      }, true);
    }

    mic.onclick = function () {
      if (recorder && recorder.state === "recording") stopRecording();
      else startRecording();
    };
  }

  global.SpecPilotMic = { init: init };
})(window);