import { loadUserProfile, setupUserProfile } from "./profile.js";
import { renderDescription } from "./description.js";
import { renderPRD } from "./prd.js";
import { displayTasks } from "./tasks.js";
import { renderSprint } from "./sprint.js";
import { parseJSONIfPossible } from "./utils.js";

console.log("🔥 PROJECT DETAILS CONTROLLER LOADED 🔥");
console.log("=================================");
console.log("PROJECT DETAILS DEBUG");
console.log("FULL URL:", window.location.href);
console.log("QUERY STRING:", window.location.search);
console.log("Project ID:", getProjectId());
console.log(
    "Stored Project ID:",
    localStorage.getItem("selected_project_id")
);
console.log("Access token exists:", !!localStorage.getItem("access_token"));
console.log("=================================");
const API_URL = "http://127.0.0.1:8000";

let currentProject = null;
let generatedContent = null;

// =========================================================
// PAGE LOAD
// =========================================================

document.addEventListener("DOMContentLoaded", async () => {
    console.log("=================================");
    console.log("PROJECT DETAILS PAGE");
    console.log("=================================");

    if (!checkAuthentication()) {
        return;
    }

    setupNavigation();
    setupButtons();
    setupTabs();
    setupEditButtons();
    setupUserProfile();
    loadUserProfile();

    await loadProject();
});

// =========================================================
// AUTHENTICATION
// =========================================================

function checkAuthentication() {
    const token = localStorage.getItem("access_token");

    if (!token) {
        console.error("No access token found.");
        window.location.href = "../index.html";
        return false;
    }

    return true;
}

function getAccessToken() {
    return localStorage.getItem("access_token");
}

// =========================================================
// PROJECT ID
// =========================================================

function getProjectId() {
    const params =
        new URLSearchParams(
            window.location.search
        );

    const urlProjectId =
        params.get("id") ||
        params.get("project_id");

    const storedProjectId =
        localStorage.getItem(
            "selected_project_id"
        );

    return (
        urlProjectId ||
        storedProjectId ||
        null
    );
}

// =========================================================
// LOAD PROJECT
// =========================================================

async function loadProject() {
    const projectId = getProjectId();
    const accessToken = getAccessToken();

    console.log("=================================");
    console.log("PROJECT DETAILS DEBUG");
    console.log("Project ID:", projectId);
    console.log("Access token exists:", !!accessToken);
    console.log("=================================");

    if (!projectId) {
        showError("Project ID is missing.");
        return;
    }

    if (!accessToken) {
        showError("Access token is missing. Please login again.");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/projects/${projectId}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json"
            }
        });

        console.log("Project API status:", response.status);

        const responseText = await response.text();

        if (!response.ok) {
            throw new Error(`Failed to load project (${response.status})`);
        }

        const project = JSON.parse(responseText);
        console.log("Project loaded:", project);

        currentProject = project;

        renderSavedPRD(project);
        displayProject(project);
        renderOriginalProject(project);
        renderExistingProjectData(project);
        updateGenerationButtonVisibility(project);

        await loadGeneratedAIContent(projectId, accessToken);

    } catch (error) {
        console.error("Error loading project:", error);
        showError(error.message || "Failed to load project.");
    }
}

// =========================================================
// SHOW/HIDE GENERATE BUTTON BASED ON EXISTING PRD
// =========================================================
//
// If a PRD already exists on the project (product_overview is the
// first field PRDGenerator validates, so its presence means a full
// generation run already completed), there's no reason to call the
// LLM again — hide the button and let the saved content speak for
// itself. If the person genuinely wants to regenerate everything,
// they can be given an explicit "Regenerate" affordance later; for
// now this simply prevents an accidental duplicate LLM call.
// =========================================================

function updateGenerationButtonVisibility(project) {

    const generatePrdButton =
        document.getElementById("generatePrdButton");

    if (!generatePrdButton) {
        return;
    }

    const alreadyGenerated =
        project.product_overview !== null &&
        project.product_overview !== undefined &&
        String(project.product_overview).trim() !== "";

    if (alreadyGenerated) {

        generatePrdButton.classList.add("hidden");

    } else {

        generatePrdButton.classList.remove("hidden");

    }
}

// =========================================================
// PROJECT HEADER
// =========================================================

function displayProject(project) {
    const loadingState = document.getElementById("loadingState");
    const projectContent = document.getElementById("projectContent");

    if (loadingState) loadingState.classList.add("hidden");
    if (projectContent) projectContent.classList.remove("hidden");

    setText("projectName", project.project_name || "Untitled Project");
    setText("breadcrumbProjectName", project.project_name || "Project");
    setText("projectIdText", project.id ? `Project ID: ${project.id}` : "");
    setText("projectShortDescription", project.business_objective || "No business objective provided.");
}

// =========================================================
// ORIGINAL PROJECT INFORMATION
// =========================================================

function renderOriginalProject(project) {
    console.log("Rendering ORIGINAL project information...");

    setOriginalValue("originalBusinessObjective", project.business_objective);
    setOriginalValue("originalTargetUsers", project.target_users);
    setOriginalValue("originalProblemStatement", project.problem_statement);
    setOriginalValue("originalExpectedFeatures", project.expected_features);
    setOriginalValue("originalTechnologyPreferences", project.technology_preferences);
    setOriginalValue("originalTimeline", project.timeline);
    setOriginalValue("originalAdditionalInstructions", project.additional_instructions);
}

// =========================================================
// EXISTING PROJECT GENERATED FIELDS
// =========================================================

function renderExistingProjectData(project) {
    console.log("Checking generated fields stored on project...");

    if (project.sprint_plan) {
        renderSprint(project.sprint_plan);
        setStatus("sprintStatus", "Generated");
    }

    if (project.tasks) {
        let tasks = project.tasks;
        if (typeof tasks === "string") {
            tasks = parseJSONIfPossible(tasks);
        }
        if (Array.isArray(tasks)) {
            displayTasks(tasks);
            setStatus("tasksStatus", "Generated");
        }
    }
}

// =========================================================
// LOAD SAVED AI CONTENT
// =========================================================

async function loadGeneratedAIContent(projectId, accessToken) {
    try {
        console.log("Loading generated AI content...");

        const response = await fetch(`${API_URL}/ai/generated/${projectId}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json"
            }
        });

        console.log("AI content API status:", response.status);

        if (!response.ok) {
            console.log("No generated AI content found yet.");
            return;
        }

        const data = await response.json();
        console.log("Generated AI content:", data);

        generatedContent = data;
        renderAIContent(data);

    } catch (error) {
        console.log("AI content could not be loaded:", error);
    }
}

// =========================================================
// RENDER SAVED AI CONTENT
// =========================================================

function renderAIContent(data) {
    console.log("=================================");
    console.log("RENDERING AI GENERATED CONTENT");
    console.log("=================================");

    if (!data || typeof data !== "object") {
        console.warn("AI response is empty or invalid.");
        return;
    }

    // AI DESCRIPTION
    const aiDescription = data.description;
    if (aiDescription && typeof aiDescription === "object") {
        console.log("Rendering AI Description:", aiDescription);
        renderDescription(aiDescription);
        setStatus("descriptionStatus", "Generated");
    }

    // AI PRD
    const aiPrd = data.prd;
    if (aiPrd && typeof aiPrd === "object") {
        console.log("Rendering AI PRD:", aiPrd);
        renderPRD(aiPrd);
        setStatus("prdStatus", "Generated");
    }

    // AI TASKS
    let aiTasks = data.tasks;
    if (typeof aiTasks === "string") {
        aiTasks = parseJSONIfPossible(aiTasks);
    }
    if (Array.isArray(aiTasks)) {
        console.log("Rendering AI Tasks:", aiTasks);
        displayTasks(aiTasks);
        setStatus("tasksStatus", "Generated");
    }

    // AI SPRINT PLAN
    const aiSprintPlan = data.sprint_plan || data.sprint || data.sprintPlan || "";
    if (aiSprintPlan) {
        console.log("Rendering AI Sprint Plan.");
        renderSprint(aiSprintPlan);
        setStatus("sprintStatus", "Generated");
    }
}

// =========================================================
// BUTTON SETUP
// =========================================================

function setupButtons() {
    const generatePrdButton = document.getElementById("generatePrdButton");

    // NOTE: generateDescription / generateTasks / generateSprint
    // buttons and their handlers are left exactly as before, for
    // manually re-running an individual stage. generatePrdButton is
    // now the "run everything" entry point (renamed in behavior,
    // not in markup) — it calls the combined /generation/run
    // pipeline instead of the old single-stage /ai/generate-prd.

    const descriptionButton = document.getElementById("generateDescriptionButton");
    const tasksButton = document.getElementById("generateTasksButton");
    const sprintButton = document.getElementById("generateSprintButton");

    if (descriptionButton) descriptionButton.addEventListener("click", generateDescription);
    if (tasksButton) tasksButton.addEventListener("click", generateTasks);
    if (sprintButton) sprintButton.addEventListener("click", generateSprint);
    if (generatePrdButton) generatePrdButton.addEventListener("click", runFullGenerationPipeline);

    // DOWNLOAD PRD
    const downloadPrdButton = document.getElementById("downloadPrdButton");
    const downloadPrdMenu = document.getElementById("downloadPrdMenu");
    const downloadPrdPdfOption = document.getElementById("downloadPrdPdfOption");
    const downloadPrdDocxOption = document.getElementById("downloadPrdDocxOption");

    if (downloadPrdButton && downloadPrdMenu) {
        downloadPrdButton.addEventListener("click", (event) => {
            event.stopPropagation();
            downloadPrdMenu.classList.toggle("hidden");
        });

        document.addEventListener("click", () => {
            downloadPrdMenu.classList.add("hidden");
        });

        downloadPrdMenu.addEventListener("click", (event) => {
            event.stopPropagation();
        });
    }

    if (downloadPrdPdfOption) {
        downloadPrdPdfOption.addEventListener("click", () => {
            if (downloadPrdMenu) downloadPrdMenu.classList.add("hidden");
            downloadPRD("pdf");
        });
    }

    if (downloadPrdDocxOption) {
        downloadPrdDocxOption.addEventListener("click", () => {
            if (downloadPrdMenu) downloadPrdMenu.classList.add("hidden");
            downloadPRD("docx");
        });
    }
}

// =========================================================
// GENERATE DESCRIPTION
// =========================================================

async function generateDescription() {
    const projectId = currentProject?.id || getProjectId();
    const accessToken = getAccessToken();

    if (!projectId) {
        showError("Project ID is missing.");
        return;
    }

    if (!accessToken) {
        showError("Access token is missing.");
        return;
    }

    const button = document.getElementById("generateDescriptionButton");
    const status = document.getElementById("descriptionStatus");

    try {
        console.log("=================================");
        console.log("GENERATING AI DESCRIPTION");
        console.log("PROJECT ID:", projectId);
        console.log("=================================");

        if (button) {
            button.disabled = true;
            button.innerHTML = `
                <span class="material-symbols-outlined animate-spin text-[18px]">
                    progress_activity
                </span>
                Generating...
            `;
        }

        if (status) status.textContent = "Generating AI description...";

        const response = await fetch(`${API_URL}/ai/generate-description/${projectId}`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json"
            }
        });

        const text = await response.text();
        let data;

        try {
            data = JSON.parse(text);
        } catch {
            throw new Error(text || "Invalid response from description API.");
        }

        if (!response.ok) {
            throw new Error(data.detail || data.message || "Description generation failed.");
        }

        if (!data.description || typeof data.description !== "object") {
            throw new Error("Backend did not return a valid AI description.");
        }

        renderDescription(data.description);
        setStatus("descriptionStatus", "Generated");

    } catch (error) {
        console.error("DESCRIPTION GENERATION ERROR:", error);
        if (status) {
            status.textContent = error.message || "Something went wrong while generating the description.";
        }
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = `
                <span class="material-symbols-outlined text-[18px]">
                    auto_awesome
                </span>
                Generate Description
            `;
        }
    }
}

// =========================================================
// RUN FULL GENERATION PIPELINE (PRD + TASKS + SPRINT PLAN)
// =========================================================
//
// Calls POST /generation/run/{project_id} — the combined Generation
// Manager endpoint — instead of the old single-stage
// /ai/generate-prd/{projectId}. Renders description, PRD, tasks and
// sprint plan from the single response instead of requiring three
// more separate button clicks afterward.
// =========================================================

async function runFullGenerationPipeline() {
    const projectId = currentProject?.id || getProjectId();
    const accessToken = getAccessToken();

    if (!projectId || !accessToken) {
        showError("Project information or authentication is missing.");
        return;
    }

    const button = document.getElementById("generatePrdButton");
    const status = document.getElementById("prdStatus");

    try {
        if (button) {
            button.disabled = true;
            button.innerHTML = `
                <span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                Generating...
            `;
        }

        if (status) status.textContent = "Generating PRD, tasks, and sprint plan...";

        const response = await fetch(`${API_URL}/generation/run/${projectId}`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Accept": "application/json"
            }
        });

        const text = await response.text();
        let data;

        try {
            data = JSON.parse(text);
        } catch {
            throw new Error(text || "Invalid response from generation pipeline.");
        }

        if (!response.ok) {
            throw new Error(data.detail || data.message || "Generation failed.");
        }

        console.log("=================================");
        console.log("GENERATION PIPELINE RESULT");
        console.log("=================================");
        console.log(data);

        if (data.description && typeof data.description === "object") {
            renderDescription(data.description);
            setStatus("descriptionStatus", "Generated");
        }

        if (data.prd && typeof data.prd === "object") {
            renderPRD(data.prd);
            setStatus("prdStatus", "Generated");
        }

        if (data.sprint_plan) {
            renderSprint(data.sprint_plan);
            setStatus("sprintStatus", "Generated");
        }

        if (typeof data.tasks_created === "number") {
            setStatus("tasksStatus", `Generated (${data.tasks_created})`);
        }

        // Hide the button now that generation succeeded — refresh
        // currentProject's PRD field locally so a re-render (e.g. a
        // tab switch) doesn't show the button again without a reload.
        if (currentProject) {
            currentProject.product_overview =
                (data.prd && data.prd.product_overview) || currentProject.product_overview;
        }

        if (button) {
            button.classList.add("hidden");
        }

    } catch (error) {
        console.error("GENERATION PIPELINE ERROR:", error);
        if (status) {
            status.textContent = error.message || "Something went wrong during generation.";
        }
        if (button) {
            button.disabled = false;
            button.innerHTML = `
                <span class="material-symbols-outlined text-[18px]">auto_awesome</span>
                Generate PRD
            `;
        }
    }
}

// =========================================================
// DOWNLOAD PRD
// =========================================================

async function downloadPRD(format) {
    const projectId = currentProject?.id || getProjectId();
    const accessToken = getAccessToken();

    if (!projectId || !accessToken) {
        showError("Project information or authentication is missing.");
        return;
    }

    const buttonId = format === "docx" ? "downloadPrdDocxOption" : "downloadPrdPdfOption";
    const button = document.getElementById(buttonId);

    try {
        if (button) {
            button.style.pointerEvents = "none";
            button.style.opacity = "0.6";
        }

        const response = await fetch(`${API_URL}/projects/${projectId}/download-prd?format=${format}`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${accessToken}` }
        });

        if (!response.ok) {
            let errorMessage = "Failed to download PRD.";
            try {
                const data = await response.json();
                errorMessage = data.detail || data.message || errorMessage;
            } catch {
                // ignore
            }
            throw new Error(errorMessage);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = `${currentProject?.project_name || "project"}-PRD.${format}`;

        document.body.appendChild(link);
        link.click();
        link.remove();

        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error("PRD DOWNLOAD ERROR:", error);
        showError(error.message || "Failed to download PRD.");
    } finally {
        if (button) {
            button.style.pointerEvents = "auto";
            button.style.opacity = "1";
        }
    }
}

// =========================================================
// RENDER SAVED PRD
// =========================================================

function renderSavedPRD(project) {
    console.log("=================================");
    console.log("RENDERING SAVED PRD");
    console.log("=================================");

    const prd = {
        product_overview: project.product_overview || "",
        problem_statement: project.prd_problem_statement || "",
        goals_and_objectives: project.goals_and_objectives || "",
        target_users: project.prd_target_users || "",
        functional_requirements: project.functional_requirements || "",
        user_workflows: project.user_workflows || "",
        business_rules: project.business_rules || "",
        non_functional_requirements: project.non_functional_requirements || "",
        assumptions_and_dependencies: project.assumptions_and_dependencies || "",
        acceptance_criteria: project.acceptance_criteria || ""
    };

    const hasPRD = Object.values(prd).some(
        value => value !== null && value !== undefined && String(value).trim() !== ""
    );

    if (!hasPRD) {
        console.log("No saved PRD found.");
        setStatus("prdStatus", "Not generated yet");
        return;
    }

    console.log("SAVED PRD:", prd);
    renderPRD(prd);
    setStatus("prdStatus", "Generated");
}

// =========================================================
// GENERATE TASKS
// =========================================================

async function generateTasks() {
    const projectId = currentProject?.id || getProjectId();
    const accessToken = getAccessToken();

    if (!projectId || !accessToken) {
        showError("Project information or authentication is missing.");
        return;
    }

    const button = document.getElementById("generateTasksButton");
    const status = document.getElementById("tasksStatus");

    try {
        if (button) {
            button.disabled = true;
            button.innerHTML = `
                <span class="material-symbols-outlined animate-spin text-[18px]">
                    progress_activity
                </span>
                Generating...
            `;
        }

        if (status) status.textContent = "Generating tasks...";

        const response = await fetch(`${API_URL}/ai/generate-tasks/${projectId}`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json"
            }
        });

        const text = await response.text();
        let data;

        try {
            data = JSON.parse(text);
        } catch {
            throw new Error(text || "Invalid response from Tasks API.");
        }

        if (!response.ok) {
            throw new Error(data.detail || data.message || "Task generation failed.");
        }

        if (Array.isArray(data.tasks)) {
            displayTasks(data.tasks);
            setStatus("tasksStatus", "Generated");
        }

    } catch (error) {
        console.error("TASK GENERATION ERROR:", error);
        if (status) {
            status.textContent = error.message || "Failed to generate tasks.";
        }
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = `
                <span class="material-symbols-outlined text-[18px]">
                    auto_awesome
                </span>
                Generate Tasks
            `;
        }
    }
}

// =========================================================
// GENERATE SPRINT
// =========================================================

async function generateSprint() {
    const projectId = currentProject?.id || getProjectId();
    const accessToken = getAccessToken();

    if (!projectId || !accessToken) {
        showError("Project information or authentication is missing.");
        return;
    }

    const button = document.getElementById("generateSprintButton");
    const status = document.getElementById("sprintStatus");

    try {
        if (button) {
            button.disabled = true;
            button.innerHTML = `
                <span class="material-symbols-outlined animate-spin text-[18px]">
                    progress_activity
                </span>
                Generating...
            `;
        }

        if (status) status.textContent = "Generating sprint plan...";

        const response = await fetch(`${API_URL}/ai/generate-sprint/${projectId}`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json"
            }
        });

        const text = await response.text();
        let data;

        try {
            data = JSON.parse(text);
        } catch {
            throw new Error(text || "Invalid response from Sprint API.");
        }

        if (!response.ok) {
            throw new Error(data.detail || data.message || "Sprint generation failed.");
        }

        if (data.sprint_plan) {
            renderSprint(data.sprint_plan);
            setStatus("sprintStatus", "Generated");
        }

    } catch (error) {
        console.error("SPRINT GENERATION ERROR:", error);
        if (status) {
            status.textContent = error.message || "Failed to generate sprint plan.";
        }
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = `
                <span class="material-symbols-outlined text-[18px]">
                    auto_awesome
                </span>
                Generate Sprint Plan
            `;
        }
    }
}

// =========================================================
// NAVIGATION
// =========================================================

function setupNavigation() {
    const backButton = document.getElementById("backButton");
    if (backButton) {
        backButton.addEventListener("click", () => {
            window.location.href = "dashboard.html";
        });
    }

    const newProjectButton = document.getElementById("newProjectBtn");
    if (newProjectButton) {
        newProjectButton.addEventListener("click", () => {
            window.location.href = "create-project.html";
        });
    }
}

// =========================================================
// TABS
// =========================================================

function setupTabs() {
    const tabs = document.querySelectorAll(".tab-button");

    const tabMap = {
        description: "descriptionTab",
        prd: "prdTab",
        tasks: "tasksTab",
        sprint: "sprintTab"
    };

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const target = tab.dataset.tab;
            const targetId = tabMap[target];

            if (!targetId) return;

            // RESET TABS
            tabs.forEach(item => {
                item.classList.remove("text-primary", "font-semibold");
                item.classList.add("text-on-surface-variant");
                item.classList.remove("border-primary");
                item.classList.add("border-transparent");
            });

            // HIDE PANELS
            Object.values(tabMap).forEach(id => {
                const panel = document.getElementById(id);
                if (panel) panel.classList.add("hidden");
            });

            // ACTIVATE SELECTED TAB
            tab.classList.remove("text-on-surface-variant");
            tab.classList.add("text-primary", "font-semibold");
            tab.classList.remove("border-transparent");
            tab.classList.add("border-primary");

            const panel = document.getElementById(targetId);
            if (panel) panel.classList.remove("hidden");
        });
    });
}

// =========================================================
// HELPER - SET ORIGINAL VALUE
// =========================================================

function setOriginalValue(elementId, value) {
    const element = document.getElementById(elementId);

    if (!element) {
        console.warn(`Element not found: ${elementId}`);
        return;
    }

    if (value === null || value === undefined || String(value).trim() === "") {
        element.textContent = "Not available.";
        element.classList.add("empty-content");
        return;
    }

    element.textContent = String(value);
    element.classList.remove("empty-content");
}

// =========================================================
// HELPER - SET TEXT
// =========================================================

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.textContent = value ?? "";
}

// =========================================================
// HELPER - STATUS
// =========================================================

function setStatus(elementId, text) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.textContent = text;
}

// =========================================================
// EDIT PROJECT FIELD
// =========================================================

async function editProjectField(contentId, fieldName, fieldLabel) {

    const contentElement =
        document.getElementById(contentId);

    if (!contentElement) {
        console.warn(
            `Edit target not found: ${contentId}`
        );
        return;
    }

    // Prevent opening multiple editors for the same field.
    if (
        contentElement.dataset.editing === "true"
    ) {
        return;
    }

    contentElement.dataset.editing = "true";

    const originalValue =
        getEditableContentValue(contentElement);

    const editorWrapper =
        document.createElement("div");

    editorWrapper.className =
        "space-y-3";

    editorWrapper.innerHTML = `
        <textarea
            class="
                w-full
                min-h-[140px]
                p-4
                rounded-lg
                border
                border-outline-variant
                bg-surface
                text-on-surface
                focus:outline-none
                focus:ring-2
                focus:ring-primary
                resize-y
            "
            data-edit-input
        ></textarea>

        <div class="flex justify-end gap-2">

            <button
                type="button"
                class="
                    px-3
                    py-2
                    rounded-lg
                    border
                    border-outline-variant
                    hover:bg-surface-container
                    transition-colors
                "
                data-edit-cancel
            >
                Cancel
            </button>

            <button
                type="button"
                class="
                    px-3
                    py-2
                    rounded-lg
                    bg-primary
                    text-on-primary
                    hover:opacity-90
                    transition-colors
                    flex
                    items-center
                    gap-2
                "
                data-edit-save
            >
                <span
                    class="material-symbols-outlined text-[18px]"
                >
                    save
                </span>

                Save
            </button>

        </div>
    `;

    const textarea =
        editorWrapper.querySelector(
            "[data-edit-input]"
        );

    textarea.value = originalValue;

    contentElement.innerHTML = "";
    contentElement.appendChild(
        editorWrapper
    );

    textarea.focus();

    // -----------------------------------------------------
    // CANCEL
    // -----------------------------------------------------

    const cancelButton =
        editorWrapper.querySelector(
            "[data-edit-cancel]"
        );

    cancelButton.addEventListener(
        "click",
        () => {

            contentElement.dataset.editing =
                "false";

            restoreEditableContent(
                contentElement,
                originalValue
            );
        }
    );

    // -----------------------------------------------------
    // SAVE
    // -----------------------------------------------------

    const saveButton =
        editorWrapper.querySelector(
            "[data-edit-save]"
        );

    saveButton.addEventListener(
        "click",
        async () => {

            const newValue =
                textarea.value.trim();

            if (!newValue) {

                showError(
                    `${fieldLabel} cannot be empty.`
                );

                return;
            }

            try {

                saveButton.disabled = true;

                saveButton.innerHTML = `
                    <span
                        class="
                            material-symbols-outlined
                            animate-spin
                            text-[18px]
                        "
                    >
                        progress_activity
                    </span>

                    Saving...
                `;

                const projectId =
                    currentProject?.id ||
                    getProjectId();

                const accessToken =
                    getAccessToken();

                const response =
                    await fetch(
                        `${API_URL}/projects/${projectId}/field`,
                        {
                            method: "PUT",

                            headers: {
                                "Authorization":
                                    `Bearer ${accessToken}`,

                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                field: fieldName,
                                value: newValue
                            })
                        }
                    );

                const responseText =
                    await response.text();

                let data;

                try {
                    data =
                        JSON.parse(responseText);
                } catch {
                    throw new Error(
                        responseText ||
                        "Invalid response from server."
                    );
                }

                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        data.message ||
                        `Failed to update ${fieldLabel}.`
                    );
                }

                // Update local project object.
                if (currentProject) {

                    currentProject[fieldName] =
                        data.value;
                }

                contentElement.dataset.editing =
                    "false";

                restoreEditableContent(
                    contentElement,
                    data.value
                );

                console.log(
                    `${fieldLabel} updated successfully.`
                );

            } catch (error) {

                console.error(
                    `EDIT ${fieldLabel} ERROR:`,
                    error
                );

                showError(
                    error.message ||
                    `Failed to update ${fieldLabel}.`
                );

                saveButton.disabled = false;

                saveButton.innerHTML = `
                    <span
                        class="
                            material-symbols-outlined
                            text-[18px]
                        "
                    >
                        save
                    </span>

                    Save
                `;
            }
        }
    );
}
// =========================================================
// SETUP EDIT BUTTONS
// =========================================================

function setupEditButtons() {

    const editableFields = [

        // DESCRIPTION
        {
            buttonId: "editOverviewButton",
            contentId: "overviewContent",
            field: "overview",
            label: "Overview"
        },

        {
            buttonId: "editProblemStatementButton",
            contentId: "problemStatementContent",
            field: "ai_problem_statement",
            label: "Problem Statement"
        },

        {
            buttonId: "editProposedSolutionButton",
            contentId: "proposedSolutionContent",
            field: "proposed_solution",
            label: "Proposed Solution"
        },

        {
            buttonId: "editTargetAudienceButton",
            contentId: "targetAudienceContent",
            field: "target_audience",
            label: "Target Audience"
        },

        {
            buttonId: "editBusinessValueButton",
            contentId: "businessValueContent",
            field: "business_value",
            label: "Business Value"
        },

        {
            buttonId: "editMajorFeaturesButton",
            contentId: "majorFeaturesContent",
            field: "major_features",
            label: "Major Features"
        },

        {
            buttonId: "editExpectedOutcomeButton",
            contentId: "expectedOutcomeContent",
            field: "expected_outcome",
            label: "Expected Outcome"
        },


        // PRD
        {
            buttonId: "editProductOverviewButton",
            contentId: "prdProductOverview",
            field: "product_overview",
            label: "Product Overview"
        },

        {
            buttonId: "editPRDProblemStatementButton",
            contentId: "prdProblemStatement",
            field: "prd_problem_statement",
            label: "PRD Problem Statement"
        },

        {
            buttonId: "editGoalsButton",
            contentId: "prdGoals",
            field: "goals_and_objectives",
            label: "Goals and Objectives"
        },

        {
            buttonId: "editPRDTargetUsersButton",
            contentId: "prdTargetUsers",
            field: "prd_target_users",
            label: "PRD Target Users"
        },

        {
            buttonId: "editFunctionalRequirementsButton",
            contentId: "prdFunctionalRequirements",
            field: "functional_requirements",
            label: "Functional Requirements"
        },

        {
            buttonId: "editUserWorkflowsButton",
            contentId: "prdUserWorkflows",
            field: "user_workflows",
            label: "User Workflows"
        },

        {
            buttonId: "editBusinessRulesButton",
            contentId: "prdBusinessRules",
            field: "business_rules",
            label: "Business Rules"
        },

        {
            buttonId: "editNonFunctionalRequirementsButton",
            contentId: "prdNonFunctionalRequirements",
            field: "non_functional_requirements",
            label: "Non-functional Requirements"
        },

        {
            buttonId: "editAssumptionsButton",
            contentId: "prdAssumptions",
            field: "assumptions_and_dependencies",
            label: "Assumptions and Dependencies"
        },

        {
            buttonId: "editAcceptanceCriteriaButton",
            contentId: "prdAcceptanceCriteria",
            field: "acceptance_criteria",
            label: "Acceptance Criteria"
        },

        // SPRINT PLAN
        {
            buttonId: "editSprintButton",
            contentId: "sprintContent",
            field: "sprint_plan",
            label: "Sprint Plan"
        }
    ];


    editableFields.forEach(
        ({
            buttonId,
            contentId,
            field,
            label
        }) => {

            const button =
                document.getElementById(
                    buttonId
                );

            if (!button) {
                console.warn(
                    `Edit button not found: ${buttonId}`
                );
                return;
            }

            button.addEventListener(
                "click",
                () => {
                    editProjectField(
                        contentId,
                        field,
                        label
                    );
                }
            );
        }
    );
}
// =========================================================
// ERROR
// =========================================================

function showError(message) {
    console.error(message);

    const errorState = document.getElementById("errorState");
    const errorMessage = document.getElementById("errorMessage");
    const loadingState = document.getElementById("loadingState");

    if (loadingState) loadingState.classList.add("hidden");
    if (errorState) errorState.classList.remove("hidden");
    if (errorMessage) errorMessage.textContent = message;
}