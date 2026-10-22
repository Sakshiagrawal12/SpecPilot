// =========================================================
// SPRINT PLAN RENDERER
// =========================================================
//
// renderSprint(sprintPlan) keeps the same name, signature and target
// element (#sprintContent) as before.
//
// New: if the plan text contains "Sprint N" headings, it is shown as one
// card per sprint (goal, task table, deliverables, definition of done,
// dependencies). Anything else falls back to the original marked.js
// rendering, so no content is ever lost.
// =========================================================

const SECTIONS = {
    "sprint goal": "goal",
    "goal": "goal",
    "tasks": "tasks",
    "deliverables": "deliverables",
    "dependencies": "dependencies",
    "definition of done": "done"
};

// ---------------------------------------------------------
// PARSING
// ---------------------------------------------------------

function stripMd(s) {
    return String(s)
        .replace(/^\s*#{1,6}\s*/, "")
        .replace(/\*\*|__/g, "")
        .trim();
}

function listItem(line) {
    return line
        .replace(/^[-*\u2022]\s+/, "")
        .replace(/^\d+[.)]\s+/, "")
        .trim();
}

function tableRow(line) {

    // Markdown separator row: |---|---|
    if (/^[\s|:\-]+$/.test(line)) {
        return null;
    }

    let cells;

    if (line.includes("|")) {
        cells = line.split("|").map(c => c.trim()).filter(Boolean);
    } else if (line.includes("\t")) {
        cells = line.split("\t").map(c => c.trim());
    } else {
        return null;
    }

    if (cells.length < 2) {
        return null;
    }

    // Header row
    if (/^(id|#|task id|no\.?)$/i.test(cells[0])) {
        return null;
    }

    return {
        id: cells[0],
        title: cells[1],
        owner: cells[2] || ""
    };
}

export function parseSprintPlan(text) {

    const sprints = [];
    const extra = [];

    let current = null;
    let section = null;

    const lines = String(text || "").replace(/\r/g, "").split("\n");

    for (const raw of lines) {

        let line = stripMd(raw);

        if (!line) {
            if (section === "extra") {
                extra.push("");
            }
            continue;
        }

        const isHeading = /^\s*#{1,6}\s/.test(raw);

        const sprintHeading = line.match(
            /^Sprint\s+(\d+)\s*(?:[\u2013\u2014:\-]+\s*(.+))?$/i
        );

        if (sprintHeading) {

            current = {
                number: Number(sprintHeading[1]),
                title: (sprintHeading[2] || "").trim(),
                goal: "",
                tasks: [],
                deliverables: [],
                dependencies: [],
                done: []
            };

            sprints.push(current);
            section = null;
            continue;
        }

        if (!current) {
            continue;
        }

        const label = line.replace(/:\s*$/, "").toLowerCase();

        if (SECTIONS[label]) {
            section = SECTIONS[label];
            continue;
        }

        const inline = line.match(
            /^(sprint goal|goal|deliverables|dependencies|definition of done)\s*:\s*(.+)$/i
        );

        if (inline) {
            section = SECTIONS[inline[1].toLowerCase()];
            line = inline[2];
        } else if (isHeading) {
            // A heading we do not know (for example "Capacity Assumptions"):
            // keep it and everything under it as extra Markdown.
            section = "extra";
            extra.push(raw);
            continue;
        }

        if (section === "extra") {
            extra.push(raw);
        } else if (section === "goal") {
            current.goal += (current.goal ? " " : "") + line;
        } else if (section === "tasks") {
            const row = tableRow(line);
            if (row) {
                current.tasks.push(row);
            }
        } else if (
            section === "deliverables" ||
            section === "done" ||
            section === "dependencies"
        ) {
            current[section].push(listItem(line));
        }
    }

    return {
        sprints,
        extra: extra.join("\n").trim()
    };
}

function dependencyInfo(items) {

    const text = items.join(" ");
    const head = text.split("(")[0];

    const nums = [];

    (head.match(/\b\d+\b/g) || []).forEach(n => {
        if (!nums.includes(n)) {
            nums.push(n);
        }
    });

    const paren = text.match(/\(([^)]*)\)/);

    return {
        nums,
        note: nums.length ? (paren ? paren[1] : "") : text
    };
}

// ---------------------------------------------------------
// STYLES (added once)
// ---------------------------------------------------------

const CSS = `
.spv{font:inherit;color:inherit}
.spv-summary{margin:0 0 12px;opacity:.7;font-size:14px}
.spv-card{border:1px solid rgba(127,127,127,.3);border-radius:8px;margin-bottom:14px;overflow:hidden}
.spv-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:12px 16px;cursor:pointer;background:rgba(127,127,127,.08);list-style:none}
.spv-head::-webkit-details-marker{display:none}
.spv-head:focus-visible{outline:2px solid var(--spv-accent,#4f46e5);outline-offset:-2px}
.spv-badge{background:var(--spv-accent,#4f46e5);color:#fff;border-radius:99px;padding:2px 12px;font-size:13px;font-weight:600;white-space:nowrap}
.spv-title{font-weight:600;font-size:16px;flex:1 1 200px}
.spv-count{font-size:13px;opacity:.65}
.spv-body{padding:14px 16px 16px}
.spv-label{font-size:12px;text-transform:uppercase;letter-spacing:.05em;opacity:.65;font-weight:600}
.spv-goal{border-left:3px solid var(--spv-accent,#4f46e5);padding:2px 0 2px 12px;margin-bottom:14px}
.spv-goal p{margin:2px 0 0}
.spv-tablewrap{overflow-x:auto;margin-bottom:14px}
.spv-table{width:100%;border-collapse:collapse;font-size:14px}
.spv-table th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;opacity:.65;padding:6px 10px;border-bottom:1px solid rgba(127,127,127,.3)}
.spv-table td{padding:8px 10px;border-bottom:1px solid rgba(127,127,127,.18);vertical-align:top}
.spv-table td:first-child{width:56px;font-weight:600;font-variant-numeric:tabular-nums}
.spv-owner{white-space:nowrap}
.spv-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-bottom:14px}
.spv-list{margin:6px 0 0;padding-left:20px}
.spv-list li{margin:3px 0}
.spv-deps{list-style:none;margin:6px 0 0;padding:0}
.spv-deps li{margin:3px 0}
.spv-dep-id{font-weight:600;margin-right:6px;font-variant-numeric:tabular-nums}
.spv-warn{color:#b4531a}
.spv-note{margin:6px 0 0;font-size:13px;opacity:.7}
.spv-extra{margin-top:8px}
`;

function injectStyle() {

    if (document.getElementById("spv-style")) {
        return;
    }

    const style = document.createElement("style");
    style.id = "spv-style";
    style.textContent = CSS;
    document.head.appendChild(style);
}

// ---------------------------------------------------------
// CARD RENDERING
// ---------------------------------------------------------

function el(tag, cls, text) {

    const node = document.createElement(tag);

    if (cls) {
        node.className = cls;
    }

    if (text != null) {
        node.textContent = text;
    }

    return node;
}

function plural(n, word) {
    return `${n} ${word}${n === 1 ? "" : "s"}`;
}

function listBlock(label, items) {

    const box = el("div");
    box.appendChild(el("div", "spv-label", label));

    const ul = el("ul", "spv-list");
    items.forEach(t => ul.appendChild(el("li", null, t)));

    box.appendChild(ul);
    return box;
}

function renderCards(container, parsed) {

    injectStyle();

    container.textContent = "";

    const root = el("div", "spv");
    container.appendChild(root);

    const { sprints, extra } = parsed;

    const titleById = {};
    const sprintById = {};
    let total = 0;

    sprints.forEach(s => {
        total += s.tasks.length;
        s.tasks.forEach(t => {
            titleById[t.id] = t.title;
            sprintById[t.id] = s.number;
        });
    });

    root.appendChild(
        el(
            "p",
            "spv-summary",
            `${plural(sprints.length, "sprint")}, ${plural(total, "task")}`
        )
    );

    sprints.forEach(s => {

        const card = el("details", "spv-card");
        card.open = true;

        const summary = el("summary", "spv-head");
        summary.appendChild(el("span", "spv-badge", `Sprint ${s.number}`));
        summary.appendChild(el("span", "spv-title", s.title));
        summary.appendChild(el("span", "spv-count", plural(s.tasks.length, "task")));
        card.appendChild(summary);

        const body = el("div", "spv-body");

        if (s.goal) {
            const goal = el("div", "spv-goal");
            goal.appendChild(el("div", "spv-label", "Goal"));
            goal.appendChild(el("p", null, s.goal));
            body.appendChild(goal);
        }

        if (s.tasks.length) {

            const wrap = el("div", "spv-tablewrap");
            const table = el("table", "spv-table");

            const headRow = el("tr");
            ["#", "Task", "Owner"].forEach(h =>
                headRow.appendChild(el("th", null, h))
            );

            const thead = el("thead");
            thead.appendChild(headRow);
            table.appendChild(thead);

            const tbody = el("tbody");

            s.tasks.forEach(t => {
                const tr = el("tr");
                tr.appendChild(el("td", null, t.id));
                tr.appendChild(el("td", null, t.title));
                tr.appendChild(el("td", "spv-owner", t.owner));
                tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            wrap.appendChild(table);
            body.appendChild(wrap);
        }

        if (s.deliverables.length || s.done.length) {

            const cols = el("div", "spv-cols");

            if (s.deliverables.length) {
                cols.appendChild(listBlock("Deliverables", s.deliverables));
            }

            if (s.done.length) {
                cols.appendChild(listBlock("Definition of done", s.done));
            }

            body.appendChild(cols);
        }

        if (s.dependencies.length) {

            const info = dependencyInfo(s.dependencies);

            const dep = el("div");
            dep.appendChild(el("div", "spv-label", "Depends on"));

            if (info.nums.length) {

                const ul = el("ul", "spv-deps");

                info.nums.forEach(n => {

                    const li = el("li");
                    li.appendChild(el("span", "spv-dep-id", `#${n}`));

                    if (titleById[n]) {
                        li.appendChild(document.createTextNode(titleById[n]));
                    }

                    // A dependency inside the same sprint is a planning error
                    if (sprintById[n] === s.number) {
                        li.classList.add("spv-warn");
                        li.title = "This task is in the same sprint, not an earlier one";
                    }

                    ul.appendChild(li);
                });

                dep.appendChild(ul);
            }

            if (info.note) {
                dep.appendChild(el("p", "spv-note", info.note));
            }

            body.appendChild(dep);
        }

        card.appendChild(body);
        root.appendChild(card);
    });

    // Anything after the last sprint that is not a known section
    if (extra) {

        const box = el("div", "spv-extra");

        if (typeof marked !== "undefined") {
            box.innerHTML = marked.parse(extra);
        } else {
            box.style.whiteSpace = "pre-wrap";
            box.textContent = extra;
        }

        root.appendChild(box);
    }
}

// ---------------------------------------------------------
// PUBLIC: same name and signature as before
// ---------------------------------------------------------

export function renderSprint(sprintPlan) {

    if (
        typeof sprintPlan === "object" &&
        sprintPlan !== null
    ) {

        sprintPlan = JSON.stringify(
            sprintPlan,
            null,
            2
        );
    }

    const container = document.getElementById("sprintContent");

    if (!container) {
        return;
    }

    if (
        !sprintPlan ||
        typeof sprintPlan !== "string" ||
        !sprintPlan.trim()
    ) {

        container.innerHTML = `
            <div class="empty-content">
                Content not generated yet.
            </div>
        `;

        return;
    }

    // New: structured sprint cards when the text has "Sprint N" headings
    const parsed = parseSprintPlan(sprintPlan);

    if (parsed.sprints.length) {
        renderCards(container, parsed);
        return;
    }

    // Original behaviour for anything else
    if (typeof marked === "undefined") {

        console.error(
            "marked.js is not loaded — check the script tag in project-details.html"
        );

        container.textContent = sprintPlan;

        return;
    }

    container.innerHTML = marked.parse(sprintPlan);
}