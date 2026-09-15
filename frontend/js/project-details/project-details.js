console.log("🔥 PROJECT DETAILS CONTROLLER LOADED 🔥");
const API_URL = "http://127.0.0.1:8000";
import { loadUserProfile, setupUserProfile } from "./profile.js";
import { renderDescription } from "./description.js";
import { renderPRD } from "./prd.js";
import { displayTasks } from "./tasks.js";
import { renderSprint } from "./sprint.js";
import { parseJSONIfPossible } from "./utils.js";
// =========================================================
// CONFIGURATION
// =========================================================



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

const params = new URLSearchParams(
    window.location.search
);

return (
    params.get("id") ||
    params.get("project_id")
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
console.log(
    "Access token exists:",
    !!accessToken
);
console.log("=================================");


// -----------------------------------------------------
// VALIDATION
// -----------------------------------------------------

if (!projectId) {

    showError("Project ID is missing.");

    return;
}


if (!accessToken) {

    showError(
        "Access token is missing. Please login again."
    );

    return;
}


// -----------------------------------------------------
// LOAD PROJECT FROM DATABASE
// -----------------------------------------------------

try {

    const response = await fetch(
        `${API_URL}/projects/${projectId}`,
        {
            method: "GET",

            headers: {
                "Authorization":
                    `Bearer ${accessToken}`,

                "Content-Type":
                    "application/json"
            }
        }
    );


    console.log(
        "Project API status:",
        response.status
    );


    const responseText =
        await response.text();


    if (!response.ok) {

        throw new Error(
            `Failed to load project (${response.status})`
        );
    }


    const project =
        JSON.parse(responseText);


    console.log(
        "Project loaded:",
        project
    );


    currentProject = project;

    renderSavedPRD(project);
    // -------------------------------------------------
    // DISPLAY ORIGINAL PROJECT DATA
    // -------------------------------------------------

    displayProject(project);

    renderOriginalProject(project);


    // -------------------------------------------------
    // DISPLAY EXISTING PROJECT DATA
    // -------------------------------------------------

    renderExistingProjectData(project);


    // -------------------------------------------------
    // LOAD SAVED AI CONTENT
    // -------------------------------------------------

    await loadGeneratedAIContent(
        projectId,
        accessToken
    );


} catch (error) {

    console.error(
        "Error loading project:",
        error
    );

    showError(
        error.message ||
        "Failed to load project."
    );
}

}

// =========================================================
// PROJECT HEADER
// =========================================================

function displayProject(project) {

const loadingState =
    document.getElementById("loadingState");

const projectContent =
    document.getElementById("projectContent");


if (loadingState) {

    loadingState.classList.add("hidden");
}


if (projectContent) {

    projectContent.classList.remove("hidden");
}


setText(
    "projectName",
    project.project_name ||
    "Untitled Project"
);


setText(
    "breadcrumbProjectName",
    project.project_name ||
    "Project"
);


setText(
    "projectIdText",
    project.id
        ? `Project ID: ${project.id}`
        : ""
);


setText(
    "projectShortDescription",
    project.business_objective ||
    "No business objective provided."
);

}

// =========================================================
// ORIGINAL PROJECT INFORMATION
// =========================================================
//
// IMPORTANT:
//
// These values are the ORIGINAL information entered
// by the user when creating the project.
//
// They are NOT AI generated.
//
// =========================================================

function renderOriginalProject(project) {

console.log(
    "Rendering ORIGINAL project information..."
);


setOriginalValue(
    "originalBusinessObjective",
    project.business_objective
);


setOriginalValue(
    "originalTargetUsers",
    project.target_users
);


setOriginalValue(
    "originalProblemStatement",
    project.problem_statement
);


setOriginalValue(
    "originalExpectedFeatures",
    project.expected_features
);


setOriginalValue(
    "originalTechnologyPreferences",
    project.technology_preferences
);


setOriginalValue(
    "originalTimeline",
    project.timeline
);


setOriginalValue(
    "originalAdditionalInstructions",
    project.additional_instructions
);

}

// =========================================================
// EXISTING PROJECT GENERATED FIELDS
// =========================================================

function renderExistingProjectData(project) {

console.log(
    "Checking generated fields stored on project..."
);


// -----------------------------------------------------
// Sprint Plan
// -----------------------------------------------------

if (project.sprint_plan) {

    renderSprint(
        project.sprint_plan
    );

    setStatus(
        "sprintStatus",
        "Generated"
    );
}


// -----------------------------------------------------
// Tasks
// -----------------------------------------------------

if (project.tasks) {

    let tasks = project.tasks;


    if (typeof tasks === "string") {

        tasks =
            parseJSONIfPossible(tasks);
    }


    if (Array.isArray(tasks)) {

        displayTasks(tasks);

        setStatus(
            "tasksStatus",
            "Generated"
        );
    }
}

}

// =========================================================
// LOAD SAVED AI CONTENT
// =========================================================

async function loadGeneratedAIContent(
projectId,
accessToken
) {

try {

    console.log(
        "Loading generated AI content..."
    );


    const response = await fetch(
        `${API_URL}/ai/generated/${projectId}`,
        {
            method: "GET",

            headers: {
                "Authorization":
                    `Bearer ${accessToken}`,

                "Content-Type":
                    "application/json"
            }
        }
    );


    console.log(
        "AI content API status:",
        response.status
    );


    if (!response.ok) {

        console.log(
            "No generated AI content found yet."
        );

        return;
    }


    const data =
        await response.json();


    console.log(
        "Generated AI content:",
        data
    );


    generatedContent = data;


    renderAIContent(data);


} catch (error) {

    console.log(
        "AI content could not be loaded:",
        error
    );
}

}

// =========================================================
// RENDER SAVED AI CONTENT
// =========================================================

function renderAIContent(data) {

console.log(
    "================================="
);

console.log(
    "RENDERING AI GENERATED CONTENT"
);

console.log(
    "================================="
);


if (!data || typeof data !== "object") {

    console.warn(
        "AI response is empty or invalid."
    );

    return;
}


// -----------------------------------------------------
// AI DESCRIPTION
// -----------------------------------------------------

const aiDescription =
    data.description;


if (
    aiDescription &&
    typeof aiDescription === "object"
) {

    console.log(
        "Rendering AI Description:",
        aiDescription
    );


    renderDescription(
        aiDescription
    );


    setStatus(
        "descriptionStatus",
        "Generated"
    );
}


// -----------------------------------------------------
// AI TASKS
// -----------------------------------------------------

let aiTasks =
    data.tasks;


if (typeof aiTasks === "string") {

    aiTasks =
        parseJSONIfPossible(aiTasks);
}


if (Array.isArray(aiTasks)) {

    console.log(
        "Rendering AI Tasks:",
        aiTasks
    );


    displayTasks(
        aiTasks
    );


    setStatus(
        "tasksStatus",
        "Generated"
    );
}


// -----------------------------------------------------
// AI SPRINT PLAN
// -----------------------------------------------------

const aiSprintPlan =
    data.sprint_plan ||
    data.sprint ||
    data.sprintPlan ||
    "";


if (aiSprintPlan) {

    console.log(
        "Rendering AI Sprint Plan."
    );


    renderSprint(
        aiSprintPlan
    );


    setStatus(
        "sprintStatus",
        "Generated"
    );
}

}

// =========================================================
// BUTTON SETUP
// =========================================================
//
// Each button calls its OWN backend endpoint.
//
// Description:
// POST /ai/generate-description/{project_id}
//
// PRD:
// POST /ai/generate-prd/{project_id}
//
// Tasks:
// POST /ai/generate-tasks/{project_id}
//
// Sprint:
// POST /ai/generate-sprint/{project_id}
//
// =========================================================

function setupButtons() {

    const descriptionButton =
        document.getElementById(
            "generateDescriptionButton"
        );


    const tasksButton =
        document.getElementById(
            "generateTasksButton"
        );


    const sprintButton =
        document.getElementById(
            "generateSprintButton"
        );


    // -----------------------------------------------------
    // DESCRIPTION
    // -----------------------------------------------------

    if (descriptionButton) {

        descriptionButton.addEventListener(
            "click",
            generateDescription
        );
    }


    // -----------------------------------------------------
    // TASKS
    // -----------------------------------------------------

    if (tasksButton) {

        tasksButton.addEventListener(
            "click",
            generateTasks
        );
    }


    // -----------------------------------------------------
    // SPRINT
    // -----------------------------------------------------

    if (sprintButton) {

        sprintButton.addEventListener(
            "click",
            generateSprint
        );
    }


    // -----------------------------------------------------
    // DOWNLOAD PRD
    // -----------------------------------------------------
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
        downloadPrdMenu.classList.add("hidden");
        downloadPRD("pdf");
    });
}

if (downloadPrdDocxOption) {
    downloadPrdDocxOption.addEventListener("click", () => {
        downloadPrdMenu.classList.add("hidden");
        downloadPRD("docx");
    });
}
  // -----------------------------------------------------
    // GENERATE PRD
    // -----------------------------------------------------

    const generatePrdButton =
        document.getElementById(
            "generatePrdButton"
        );


    if (generatePrdButton) {

        generatePrdButton.addEventListener(
            "click",
            generatePRD
        );
    }

}
// =========================================================
// GENERATE DESCRIPTION
// =========================================================
//
// The frontend sends ONLY the project ID.
//
// The backend gets the complete project from the database.
//
// description.py then sends:
//
// project_name
// category
// business_objective
// target_users
// problem_statement
// expected_features
// technology_preferences
// timeline
// additional_instructions
//
// to the LLM.
//
// =========================================================

async function generateDescription() {

const projectId =
    currentProject?.id ||
    getProjectId();

const accessToken =
    getAccessToken();


if (!projectId) {

    showError(
        "Project ID is missing."
    );

    return;
}


if (!accessToken) {

    showError(
        "Access token is missing."
    );

    return;
}


const button =
    document.getElementById(
        "generateDescriptionButton"
    );


const status =
    document.getElementById(
        "descriptionStatus"
    );


try {

    console.log(
        "================================="
    );

    console.log(
        "GENERATING AI DESCRIPTION"
    );

    console.log(
        "PROJECT ID:",
        projectId
    );

    console.log(
        "================================="
    );


    // -------------------------------------------------
    // Loading state
    // -------------------------------------------------

    if (button) {

        button.disabled = true;

        button.innerHTML = `
            <span class="material-symbols-outlined animate-spin text-[18px]">
                progress_activity
            </span>
            Generating...
        `;
    }


    if (status) {

        status.textContent =
            "Generating AI description...";
    }


    // -------------------------------------------------
    // CALL CORRECT BACKEND ENDPOINT
    // -------------------------------------------------

    const response =
        await fetch(
            `${API_URL}/ai/generate-description/${projectId}`,
            {
                method: "POST",

                headers: {
                    "Authorization":
                        `Bearer ${accessToken}`,

                    "Content-Type":
                        "application/json"
                }
            }
        );


    console.log(
        "DESCRIPTION API STATUS:",
        response.status
    );


    const text =
        await response.text();


    console.log(
        "DESCRIPTION RAW RESPONSE:",
        text
    );


    let data;


    try {

        data =
            JSON.parse(text);

    } catch {

        throw new Error(
            text ||
            "Invalid response from description API."
        );
    }


    // -------------------------------------------------
    // BACKEND ERROR
    // -------------------------------------------------

    if (!response.ok) {

        throw new Error(
            data.detail ||
            data.message ||
            "Description generation failed."
        );
    }


    console.log(
        "DESCRIPTION GENERATED:",
        data
    );


    // -------------------------------------------------
    // VALIDATE DESCRIPTION
    // -------------------------------------------------

    if (
        !data.description ||
        typeof data.description !== "object"
    ) {

        throw new Error(
            "Backend did not return a valid AI description."
        );
    }


    // -------------------------------------------------
    // RENDER ONLY AI DESCRIPTION
    // -------------------------------------------------

    renderDescription(
        data.description
    );


    setStatus(
        "descriptionStatus",
        "Generated"
    );


    console.log(
        "================================="
    );

    console.log(
        "AI DESCRIPTION GENERATED SUCCESSFULLY"
    );

    console.log(
        "================================="
    );


} catch (error) {

    console.error(
        "DESCRIPTION GENERATION ERROR:",
        error
    );


    if (status) {

        status.textContent =
            error.message ||
            "Something went wrong while generating the description.";
    }

} finally {

    // -------------------------------------------------
    // Restore button
    // -------------------------------------------------

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
async function generatePRD() {

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

        if (status) status.textContent = "Generating PRD...";

        const response = await fetch(
            `${API_URL}/ai/generate-prd/${projectId}`,
            {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${accessToken}`,
                    "Content-Type": "application/json"
                }
            }
        );

        const text = await response.text();
        let data;

        try {
            data = JSON.parse(text);
        } catch {
            throw new Error(text || "Invalid response from PRD API.");
        }

        if (!response.ok) {
            throw new Error(data.detail || data.message || "PRD generation failed.");
        }

        console.log("PRD GENERATED:", data);

        if (!data.prd || typeof data.prd !== "object") {
            throw new Error("Backend did not return a valid PRD.");
        }

        renderPRD(data.prd);
        setStatus("prdStatus", "Generated");

    } catch (error) {

        console.error("PRD GENERATION ERROR:", error);

        if (status) {
            status.textContent = error.message || "Something went wrong while generating the PRD.";
        }

    } finally {

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
// Download PRD
// =========================================================
async function downloadPRD(format) {

    const projectId = currentProject?.id || getProjectId();
    const accessToken = getAccessToken();

    if (!projectId || !accessToken) {
        showError("Project information or authentication is missing.");
        return;
    }

    const buttonId = format === "docx"
        ? "downloadPrdDocxButton"
        : "downloadPrdPdfButton";

    const button = document.getElementById(buttonId);

    try {

        if (button) {
            button.disabled = true;
            button.innerHTML = `
                <span class="material-symbols-outlined animate-spin">progress_activity</span>
                <span>Preparing...</span>
            `;
        }

        const response = await fetch(
            `${API_URL}/projects/${projectId}/download-prd?format=${format}`,
            {
                method: "GET",
                headers: { "Authorization": `Bearer ${accessToken}` }
            }
        );

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
            button.disabled = false;

            const label = format === "docx" ? "Download DOCX" : "Download PDF";

            button.innerHTML = `
                <span class="material-symbols-outlined">download</span>
                <span>${label}</span>
            `;
        }
    }
}

function renderSavedPRD(project) {

    console.log(
        "================================="
    );

    console.log(
        "RENDERING SAVED PRD"
    );

    console.log(
        "================================="
    );


    const prd = {

        product_overview:
            project.product_overview || "",

        problem_statement:
            project.prd_problem_statement || "",

        goals_and_objectives:
            project.goals_and_objectives || "",

        target_users:
            project.prd_target_users || "",

        functional_requirements:
            project.functional_requirements || "",

        user_workflows:
            project.user_workflows || "",

        business_rules:
            project.business_rules || "",

        non_functional_requirements:
            project.non_functional_requirements || "",

        assumptions_and_dependencies:
            project.assumptions_and_dependencies || "",

        acceptance_criteria:
            project.acceptance_criteria || ""
    };


    const hasPRD =
        Object.values(prd).some(
            value =>
                value !== null &&
                value !== undefined &&
                String(value).trim() !== ""
        );


    if (!hasPRD) {

        console.log(
            "No saved PRD found."
        );

        setStatus(
            "prdStatus",
            "Not generated yet"
        );

        return;
    }


    console.log(
        "SAVED PRD:",
        prd
    );


    renderPRD(
        prd
    );


    setStatus(
        "prdStatus",
        "Generated"
    );

}

// =========================================================
// GENERATE TASKS
// =========================================================

async function generateTasks() {

const projectId =
    currentProject?.id ||
    getProjectId();

const accessToken =
    getAccessToken();


if (!projectId || !accessToken) {

    showError(
        "Project information or authentication is missing."
    );

    return;
}


const button =
    document.getElementById(
        "generateTasksButton"
    );


const status =
    document.getElementById(
        "tasksStatus"
    );


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


    if (status) {

        status.textContent =
            "Generating tasks...";
    }


    const response =
        await fetch(
            `${API_URL}/ai/generate-tasks/${projectId}`,
            {
                method: "POST",

                headers: {
                    "Authorization":
                        `Bearer ${accessToken}`,

                    "Content-Type":
                        "application/json"
                }
            }
        );


    const text =
        await response.text();


    let data;


    try {

        data =
            JSON.parse(text);

    } catch {

        throw new Error(
            text ||
            "Invalid response from Tasks API."
        );
    }


    if (!response.ok) {

        throw new Error(
            data.detail ||
            data.message ||
            "Task generation failed."
        );
    }


    console.log(
        "TASKS GENERATED:",
        data
    );


    if (Array.isArray(data.tasks)) {

        displayTasks(
            data.tasks
        );

        setStatus(
            "tasksStatus",
            "Generated"
        );
    }


} catch (error) {

    console.error(
        "TASK GENERATION ERROR:",
        error
    );


    if (status) {

        status.textContent =
            error.message ||
            "Failed to generate tasks.";
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

const projectId =
    currentProject?.id ||
    getProjectId();

const accessToken =
    getAccessToken();


if (!projectId || !accessToken) {

    showError(
        "Project information or authentication is missing."
    );

    return;
}


const button =
    document.getElementById(
        "generateSprintButton"
    );


const status =
    document.getElementById(
        "sprintStatus"
    );


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


    if (status) {

        status.textContent =
            "Generating sprint plan...";
    }


    const response =
        await fetch(
            `${API_URL}/ai/generate-sprint/${projectId}`,
            {
                method: "POST",

                headers: {
                    "Authorization":
                        `Bearer ${accessToken}`,

                    "Content-Type":
                        "application/json"
                }
            }
        );


    const text =
        await response.text();


    let data;


    try {

        data =
            JSON.parse(text);

    } catch {

        throw new Error(
            text ||
            "Invalid response from Sprint API."
        );
    }


    if (!response.ok) {

        throw new Error(
            data.detail ||
            data.message ||
            "Sprint generation failed."
        );
    }


    console.log(
        "SPRINT GENERATED:",
        data
    );


    if (data.sprint_plan) {

        renderSprint(
            data.sprint_plan
        );

        setStatus(
            "sprintStatus",
            "Generated"
        );
    }


} catch (error) {

    console.error(
        "SPRINT GENERATION ERROR:",
        error
    );


    if (status) {

        status.textContent =
            error.message ||
            "Failed to generate sprint plan.";
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

const backButton =
    document.getElementById(
        "backButton"
    );


if (backButton) {

    backButton.addEventListener(
        "click",
        () => {

            window.location.href =
                "dashboard.html";
        }
    );
}


const newProjectButton =
    document.getElementById(
        "newProjectBtn"
    );


if (newProjectButton) {

    newProjectButton.addEventListener(
        "click",
        () => {

            window.location.href =
                "create-project.html";
        }
    );
}

}

// =========================================================
// TABS
// =========================================================

function setupTabs() {

const tabs =
    document.querySelectorAll(
        ".tab-button"
    );


const tabMap = {

    description:
        "descriptionTab",

    prd:
        "prdTab",

    tasks:
        "tasksTab",

    sprint:
        "sprintTab"
};


tabs.forEach(tab => {

    tab.addEventListener(
        "click",
        () => {

            const target =
                tab.dataset.tab;


            const targetId =
                tabMap[target];


            if (!targetId) {

                return;
            }


            // -----------------------------------------
            // RESET TABS
            // -----------------------------------------

            tabs.forEach(item => {

                item.classList.remove(
                    "text-primary",
                    "font-semibold"
                );


                item.classList.add(
                    "text-on-surface-variant"
                );


                item.classList.remove(
                    "border-primary"
                );


                item.classList.add(
                    "border-transparent"
                );
            });


            // -----------------------------------------
            // HIDE PANELS
            // -----------------------------------------

            Object.values(tabMap)
                .forEach(id => {

                    const panel =
                        document.getElementById(id);


                    if (panel) {

                        panel.classList.add(
                            "hidden"
                        );
                    }
                });


            // -----------------------------------------
            // ACTIVATE SELECTED TAB
            // -----------------------------------------

            tab.classList.remove(
                "text-on-surface-variant"
            );


            tab.classList.add(
                "text-primary",
                "font-semibold"
            );


            tab.classList.remove(
                "border-transparent"
            );


            tab.classList.add(
                "border-primary"
            );


            const panel =
                document.getElementById(
                    targetId
                );


            if (panel) {

                panel.classList.remove(
                    "hidden"
                );
            }
        }
    );
});

}

// =========================================================
// HELPER - SET ORIGINAL VALUE
// =========================================================

function setOriginalValue(
elementId,
value
) {

const element =
    document.getElementById(
        elementId
    );


if (!element) {

    console.warn(
        `Element not found: ${elementId}`
    );

    return;
}


if (
    value === null ||
    value === undefined ||
    String(value).trim() === ""
) {

    element.textContent =
        "Not available.";

    element.classList.add(
        "empty-content"
    );

    return;
}


element.textContent =
    String(value);


element.classList.remove(
    "empty-content"
);

}

// =========================================================
// HELPER - SET TEXT
// =========================================================

function setText(
elementId,
value
) {

const element =
    document.getElementById(
        elementId
    );


if (!element) {

    return;
}


element.textContent =
    value ?? "";

}

// =========================================================
// HELPER - STATUS
// =========================================================

function setStatus(
elementId,
text
) {

const element =
    document.getElementById(
        elementId
    );


if (!element) {

    return;
}


element.textContent =
    text;

}

// =========================================================
// ERROR
// =========================================================

function showError(message) {

console.error(message);


const errorState =
    document.getElementById(
        "errorState"
    );


const errorMessage =
    document.getElementById(
        "errorMessage"
    );


const loadingState =
    document.getElementById(
        "loadingState"
    );


if (loadingState) {

    loadingState.classList.add(
        "hidden"
    );
}


if (errorState) {

    errorState.classList.remove(
        "hidden"
    );
}


if (errorMessage) {

    errorMessage.textContent =
        message;
}

}