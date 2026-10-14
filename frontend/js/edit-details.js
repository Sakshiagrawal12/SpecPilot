// ============================================================
// EDIT DETAILS MODAL
// ============================================================
//
// Put this file next to agent.js (js/edit-details.js).
//
// Opens a modal where the user can edit the project's requirement
// fields. It builds its own DOM, so agent.html only needs the
// existing #openEditModalBtn button.
//
// Backend contract (see edit_requirements_endpoints.py):
//   GET   /agent/requirements/{project_id}  -> { fields, project_name, prd_generated, ... }
//   PATCH /agent/requirements/{project_id}  -> body { fields: { <key>: <string> } }
// ============================================================

const FIELDS = [
    {
        key: "category",
        label: "Category",
        type: "input",
        placeholder: "e.g. finance, education, healthcare",
    },
    {
        key: "business_objective",
        label: "Business Objective",
        type: "textarea",
        rows: 3,
        placeholder: "The main goal or outcome of the project",
    },
    {
        key: "target_users",
        label: "Target Users",
        type: "textarea",
        rows: 3,
        placeholder: "Who will use the project",
    },
    {
        key: "problem_statement",
        label: "Problem Statement",
        type: "textarea",
        rows: 3,
        placeholder: "The problem the project solves",
    },
    {
        key: "expected_features",
        label: "Expected Features",
        type: "textarea",
        rows: 4,
        placeholder: "Key features, separated by commas or new lines",
    },
    {
        key: "technology_preferences",
        label: "Technology Preferences",
        type: "textarea",
        rows: 2,
        placeholder: "Languages, frameworks, platforms (optional)",
    },
    {
        key: "timeline",
        label: "Timeline",
        type: "input",
        placeholder: "e.g. 3 months",
    },
    {
        key: "additional_instructions",
        label: "Additional Instructions",
        type: "textarea",
        rows: 3,
        placeholder: "Anything else the PRD should consider (optional)",
    },
];

const MAX_FIELD_CHARS = 2000;

const INPUT_CLASSES =
    "w-full bg-surface-container-lowest border border-outline-variant rounded-DEFAULT " +
    "px-3 py-2 font-body-md text-body-md text-on-surface placeholder:text-outline " +
    "focus:outline-none focus:ring-2 focus:ring-primary-container/30 " +
    "focus:border-primary-container disabled:opacity-60";


function el(tag, className = "", attrs = {}) {

    const node = document.createElement(tag);

    if (className) {
        node.className = className;
    }

    Object.entries(attrs).forEach(([key, value]) => {
        node.setAttribute(key, value);
    });

    return node;
}


export function initEditDetails({
    buttonId = "openEditModalBtn",
    apiBaseUrl,
    getToken,
    getProjectId,
    isBusy = () => false,
    onSaved = async () => {},
}) {

    const button = document.getElementById(buttonId);

    if (!button) {
        console.warn(`Edit Details button #${buttonId} not found.`);
        return;
    }

    let ui = null;              // built lazily on first open
    let original = {};          // snapshot loaded from the server
    let activeProjectId = null;
    let isLoading = false;
    let isSaving = false;
    let lastFocused = null;


    button.addEventListener("click", openModal);


    // --------------------------------------------------------
    // BUILD MODAL (once)
    // --------------------------------------------------------

    function buildModal() {

        if (ui) {
            return;
        }

        const overlay = el(
            "div",
            "hidden fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4",
            { id: "editDetailsModal" }
        );

        const dialog = el(
            "div",
            "bg-surface-container-lowest rounded-xl border border-outline-variant " +
            "shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col",
            {
                role: "dialog",
                "aria-modal": "true",
                "aria-labelledby": "editDetailsTitle",
            }
        );

        // ---- header
        const header = el(
            "div",
            "flex items-start justify-between gap-4 px-6 py-4 border-b border-outline-variant"
        );

        const titleWrap = el("div");

        const title = el(
            "h3",
            "font-headline-md text-headline-md text-on-surface",
            { id: "editDetailsTitle" }
        );
        title.textContent = "Edit Project Details";

        const subtitle = el(
            "p",
            "font-body-sm text-body-sm text-on-surface-variant mt-1"
        );

        titleWrap.append(title, subtitle);

        const closeBtn = el(
            "button",
            "p-2 rounded-full text-on-surface-variant hover:bg-surface-container-high transition-colors",
            { type: "button", "aria-label": "Close" }
        );
        closeBtn.innerHTML =
            '<span class="material-symbols-outlined">close</span>';

        header.append(titleWrap, closeBtn);

        // ---- body
        const body = el("div", "px-6 py-4 overflow-y-auto space-y-4");

        const notice = el(
            "div",
            "hidden rounded-DEFAULT border border-outline-variant bg-secondary-container " +
            "text-on-secondary-container px-3 py-2 font-body-sm text-body-sm"
        );

        const loading = el(
            "div",
            "hidden font-body-sm text-body-sm text-on-surface-variant py-6 text-center"
        );
        loading.textContent = "Loading details...";

        const inputs = {};

        const fieldsWrap = el("div", "space-y-4");

        FIELDS.forEach((field) => {

            const group = el("div");

            const id = `editField_${field.key}`;

            const label = el(
                "label",
                "block font-label-md text-label-md text-on-surface mb-1",
                { for: id }
            );
            label.textContent = field.label;

            const control =
                field.type === "textarea"
                    ? el("textarea", INPUT_CLASSES + " resize-y", {
                          id,
                          rows: String(field.rows || 3),
                          maxlength: String(MAX_FIELD_CHARS),
                          placeholder: field.placeholder || "",
                      })
                    : el("input", INPUT_CLASSES, {
                          id,
                          type: "text",
                          maxlength: String(MAX_FIELD_CHARS),
                          placeholder: field.placeholder || "",
                      });

            inputs[field.key] = control;

            group.append(label, control);
            fieldsWrap.append(group);
        });

        body.append(notice, loading, fieldsWrap);

        // ---- footer
        const footer = el(
            "div",
            "px-6 py-4 border-t border-outline-variant flex items-center justify-between gap-3"
        );

        const errorEl = el(
            "p",
            "text-error font-body-sm text-body-sm min-h-[20px] flex-1",
            { role: "alert" }
        );

        const actions = el("div", "flex items-center gap-2 flex-shrink-0");

        const cancelBtn = el(
            "button",
            "px-4 py-2 border border-outline-variant rounded-DEFAULT font-label-md " +
            "text-label-md text-on-surface hover:bg-surface-container-high transition-colors",
            { type: "button" }
        );
        cancelBtn.textContent = "Cancel";

        const saveBtn = el(
            "button",
            "px-4 py-2 rounded-DEFAULT font-label-md text-label-md bg-primary-container " +
            "text-on-primary hover:bg-primary transition-colors shadow-sm " +
            "disabled:opacity-60 disabled:cursor-not-allowed",
            { type: "button" }
        );
        saveBtn.textContent = "Save changes";

        actions.append(cancelBtn, saveBtn);
        footer.append(errorEl, actions);

        dialog.append(header, body, footer);
        overlay.append(dialog);
        document.body.append(overlay);

        ui = {
            overlay,
            dialog,
            subtitle,
            notice,
            loading,
            fieldsWrap,
            inputs,
            errorEl,
            saveBtn,
            cancelBtn,
            closeBtn,
        };

        // ---- events
        closeBtn.addEventListener("click", () => closeModal());
        cancelBtn.addEventListener("click", () => closeModal());
        saveBtn.addEventListener("click", save);

        overlay.addEventListener("mousedown", (event) => {
            if (event.target === overlay) {
                closeModal();
            }
        });

        overlay.addEventListener("keydown", onKeyDown);
    }


    // --------------------------------------------------------
    // KEYBOARD: Esc closes, Ctrl/Cmd+Enter saves, Tab stays inside
    // --------------------------------------------------------

    function onKeyDown(event) {

        if (event.key === "Escape") {
            event.preventDefault();
            closeModal();
            return;
        }

        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            save();
            return;
        }

        if (event.key !== "Tab") {
            return;
        }

        const focusable = [
            ...ui.dialog.querySelectorAll(
                "button:not([disabled]), input:not([disabled]), textarea:not([disabled])"
            ),
        ];

        if (!focusable.length) {
            return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    }


    // --------------------------------------------------------
    // STATE HELPERS
    // --------------------------------------------------------

    function setError(message) {
        ui.errorEl.textContent = message || "";
    }

    function setControlsDisabled(disabled) {
        FIELDS.forEach((field) => {
            ui.inputs[field.key].disabled = disabled;
        });
        ui.saveBtn.disabled = disabled;
    }

    function setLoading(value) {
        isLoading = value;
        ui.loading.classList.toggle("hidden", !value);
        ui.fieldsWrap.classList.toggle("hidden", value);
        setControlsDisabled(value);
    }

    function setSaving(value) {
        isSaving = value;
        setControlsDisabled(value);
        ui.cancelBtn.disabled = value;
        ui.saveBtn.textContent = value ? "Saving..." : "Save changes";
    }

    function readChanges() {

        const changes = {};

        FIELDS.forEach((field) => {

            const current = ui.inputs[field.key].value.trim();
            const before = (original[field.key] || "").trim();

            if (current !== before) {
                changes[field.key] = current;
            }
        });

        return changes;
    }

    function isDirty() {
        return Object.keys(readChanges()).length > 0;
    }

    function labelFor(key) {
        return FIELDS.find((f) => f.key === key)?.label || key;
    }

    function errorMessageFrom(detail, fallback) {

        if (!detail) {
            return fallback;
        }

        if (typeof detail === "string") {
            return detail;
        }

        try {
            return JSON.stringify(detail);
        } catch {
            return fallback;
        }
    }


    // --------------------------------------------------------
    // OPEN
    // --------------------------------------------------------

    async function openModal() {

        const projectId = getProjectId();

        if (!projectId) {
            alert("Please select a project first.");
            return;
        }

        if (isBusy()) {
            alert("Please wait for the agent to finish responding.");
            return;
        }

        buildModal();

        activeProjectId = projectId;
        lastFocused = document.activeElement;

        setError("");
        ui.notice.classList.add("hidden");
        ui.subtitle.textContent = "";

        ui.overlay.classList.remove("hidden");
        document.body.style.overflow = "hidden";

        setLoading(true);

        try {

            const response = await fetch(
                `${apiBaseUrl}/agent/requirements/${projectId}`,
                {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${getToken()}`,
                        "Accept": "application/json",
                    },
                }
            );

            if (response.status === 401) {
                throw new Error("Your session expired. Please log in again.");
            }

            if (!response.ok) {
                let detail = "";
                try {
                    detail = (await response.json()).detail;
                } catch {
                    // ignore
                }
                throw new Error(
                    errorMessageFrom(detail, `Failed to load details (${response.status})`)
                );
            }

            const data = await response.json();

            original = { ...(data.fields || {}) };

            FIELDS.forEach((field) => {
                ui.inputs[field.key].value = original[field.key] || "";
            });

            ui.subtitle.textContent = data.project_name || "";

            if (data.prd_generated) {
                ui.notice.textContent =
                    "A PRD has already been generated for this project. Changes here " +
                    "update the requirements but do not change the existing PRD.";
                ui.notice.classList.remove("hidden");
            }

            setLoading(false);
            ui.inputs[FIELDS[0].key].focus();

        } catch (error) {

            console.error("EDIT DETAILS LOAD ERROR:", error);

            setLoading(false);
            setControlsDisabled(true);
            ui.cancelBtn.disabled = false;
            setError(error.message || "Failed to load details.");
        }
    }


    // --------------------------------------------------------
    // CLOSE
    // --------------------------------------------------------

    function closeModal(force = false) {

        if (!ui || ui.overlay.classList.contains("hidden")) {
            return;
        }

        if (isSaving) {
            return;
        }

        if (!force && !isLoading && isDirty()) {

            const discard = window.confirm(
                "You have unsaved changes. Discard them?"
            );

            if (!discard) {
                return;
            }
        }

        ui.overlay.classList.add("hidden");
        document.body.style.overflow = "";
        setError("");
        ui.cancelBtn.disabled = false;

        if (lastFocused && typeof lastFocused.focus === "function") {
            lastFocused.focus();
        }
    }


    // --------------------------------------------------------
    // SAVE
    // --------------------------------------------------------

    async function save() {

        if (isSaving || isLoading) {
            return;
        }

        if (isBusy()) {
            setError("Please wait for the agent to finish responding.");
            return;
        }

        const changes = readChanges();

        if (Object.keys(changes).length === 0) {
            closeModal(true);
            return;
        }

        const cleared = Object.entries(changes)
            .filter(([, value]) => value === "")
            .map(([key]) => labelFor(key));

        if (cleared.length > 0) {

            const proceed = window.confirm(
                `You cleared: ${cleared.join(", ")}.\n\n` +
                "The agent will ask about these again. Continue?"
            );

            if (!proceed) {
                return;
            }
        }

        setError("");
        setSaving(true);

        try {

            const response = await fetch(
                `${apiBaseUrl}/agent/requirements/${activeProjectId}`,
                {
                    method: "PATCH",
                    headers: {
                        "Authorization": `Bearer ${getToken()}`,
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ fields: changes }),
                }
            );

            if (!response.ok) {

                let detail = "";

                try {
                    detail = (await response.json()).detail;
                } catch {
                    // ignore
                }

                throw new Error(
                    errorMessageFrom(detail, `Save failed (${response.status})`)
                );
            }

            await response.json();

            setSaving(false);
            closeModal(true);

            await onSaved();

        } catch (error) {

            console.error("EDIT DETAILS SAVE ERROR:", error);

            setSaving(false);
            setError(error.message || "Failed to save changes.");
        }
    }
}