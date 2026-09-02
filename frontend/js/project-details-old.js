
console.log("=================================");
console.log("SPEC PILOT PROJECT DETAILS LOADED");
console.log("=================================");


// =========================================================
// CONFIGURATION
// =========================================================

const API_URL = "http://127.0.0.1:8000";

let currentProject = null;
let generatedContent = null;


// =========================================================
// PAGE LOAD
// =========================================================

document.addEventListener("DOMContentLoaded", async function () {

    console.log("Project Details DOM loaded.");

    // -----------------------------------------------------
    // CHECK AUTHENTICATION
    // -----------------------------------------------------

    if (!checkAuthentication()) {
        return;
    }

    // -----------------------------------------------------
    // SETUP PAGE
    // -----------------------------------------------------

    setupNavigation();
    setupButtons();
    setupTabs();
     loadUserProfile();
    // -----------------------------------------------------
    // LOAD PROJECT
    // -----------------------------------------------------

    await loadProject();
});
// =========================================================
// SIGN OUT
// =========================================================

function setupSignOut() {

    const signOutButton =
        document.getElementById("signOutBtn");


    if (!signOutButton) {
        return;
    }


    signOutButton.addEventListener(
        "click",
        () => {

            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            localStorage.removeItem("user_id");

            window.location.href =
                "../index.html";

        }
    );

}
function loadUserProfile() {

    const storedUser =
        localStorage.getItem("user");

    if (!storedUser) {
        return;
    }

    let user;

    try {
        user = JSON.parse(storedUser);
    } catch (error) {
        console.error("Invalid stored user:", error);
        return;
    }


    const name =
        user.name ||
        user.username ||
        user.full_name ||
        "User";

    const email =
        user.email ||
        "User account";


    const initial =
        name.trim().charAt(0).toUpperCase() || "U";


    const userName =
        document.getElementById("userName");

    const profileInitial =
        document.getElementById("userProfileInitial");

    const dropdownUserName =
        document.getElementById("dropdownUserName");

    const dropdownUserEmail =
        document.getElementById("dropdownUserEmail");


    if (userName) {
        userName.textContent = name;
    }

    if (profileInitial) {
        profileInitial.textContent = initial;
    }

    if (dropdownUserName) {
        dropdownUserName.textContent = name;
    }

    if (dropdownUserEmail) {
        dropdownUserEmail.textContent = email;
    }

}
// =========================================================
// AUTHENTICATION
// =========================================================

function checkAuthentication() {

    const accessToken =
        localStorage.getItem("access_token");

    const user =
        localStorage.getItem("user");

    console.log("Authentication check:");
    console.log("Access token exists:", !!accessToken);
    console.log("User exists:", !!user);

    if (!accessToken || !user) {

        console.error(
            "Authentication information missing."
        );

        window.location.href = "../index.html";

        return false;
    }

    return true;
}



    // -----------------------------------------------------
    // CLOSE WHEN CLICKING OUTSIDE
    // -----------------------------------------------------

    document.addEventListener("click", function (event) {

        if (
            !profileDropdown.contains(event.target) &&
            !profileBtn.contains(event.target)
        ) {

            profileDropdown.classList.add("hidden");

            if (profileArrow) {
                profileArrow.classList.remove("rotate-180");
            }

        }

    });


    // -----------------------------------------------------
    // SIGN OUT
    // -----------------------------------------------------

    if (signOutBtn) {

        signOutBtn.addEventListener("click", function () {

            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            localStorage.removeItem("user_id");

            window.location.href = "../index.html";

        });

    }



// =========================================================
// GET PROJECT ID
// =========================================================

function getProjectId() {

    const params =
        new URLSearchParams(
            window.location.search
        );

    const projectId =
        params.get("project_id") ||
        params.get("id");

    console.log(
        "Project ID:",
        projectId
    );

    return projectId;
}


// =========================================================
// GET ACCESS TOKEN
// =========================================================

function getAccessToken() {

    const token =
        localStorage.getItem("access_token");

    if (!token) {

        console.error(
            "Access token not found."
        );

        return null;
    }

    return token;
}


// =========================================================
// LOAD PROJECT
// =========================================================

async function loadProject() {

    const projectId =
        getProjectId();

    if (!projectId) {

        showError(
            "Project ID is missing."
        );

        return;
    }

    const accessToken =
        getAccessToken();

    if (!accessToken) {

        showError(
            "Authentication token is missing."
        );

        return;
    }

    try {

        console.log("=================================");
        console.log("LOADING PROJECT");
        console.log("PROJECT ID:", projectId);
        console.log("=================================");


        // -------------------------------------------------
        // GET BASIC PROJECT
        // -------------------------------------------------

        const response =
            await fetch(
                `${API_URL}/projects/${projectId}`,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,

                        "Accept":
                            "application/json"
                    }
                }
            );


        console.log(
            "Project response status:",
            response.status
        );


        const responseText =
            await response.text();


        console.log(
            "PROJECT RAW RESPONSE:",
            responseText
        );


        let project = null;


        try {

            project =
                responseText
                    ? JSON.parse(responseText)
                    : null;

        }
        catch (error) {

            console.error(
                "Project JSON parsing error:",
                error
            );

            throw new Error(
                "Server returned invalid project JSON."
            );
        }


        if (!response.ok) {

            throw new Error(
                project?.detail ||
                `Unable to load project. Status: ${response.status}`
            );
        }


        if (!project) {

            throw new Error(
                "Project data was empty."
            );
        }


        console.log("=================================");
        console.log("PROJECT RECEIVED");
        console.log(project);
        console.log("=================================");


        currentProject =
            project;


        // -------------------------------------------------
        // DISPLAY BASIC INFORMATION
        // -------------------------------------------------

        displayProject(
            project
        );


        // -------------------------------------------------
        // IMPORTANT
        //
        // Project response may already contain generated
        // AI fields.
        // -------------------------------------------------

        renderProjectFields(
            project
        );


        // -------------------------------------------------
        // LOAD GENERATED AI CONTENT
        //
        // This is attempted separately.
        //
        // If this endpoint currently returns 500 because
        // the backend still uses ai_description/prd,
        // the basic project page will still remain visible.
        // -------------------------------------------------

        await loadGeneratedAIContent(
            projectId,
            accessToken
        );


    }
    catch (error) {

        console.error("=================================");
        console.error("PROJECT LOAD ERROR");
        console.error(error);
        console.error("=================================");

        showError(
            error.message ||
            "Unable to load project."
        );
    }
}


// =========================================================
// DISPLAY BASIC PROJECT INFORMATION
// =========================================================

function displayProject(project) {

    console.log(
        "Displaying project:",
        project
    );


    document
        .getElementById("loadingState")
        ?.classList.add("hidden");


    document
        .getElementById("projectContent")
        ?.classList.remove("hidden");


    const projectName =
        project.project_name ||
        project.name ||
        "Untitled Project";


    setText(
        "projectName",
        projectName
    );


    setText(
        "breadcrumbProjectName",
        projectName
    );


    setText(
        "projectIdText",
        `Project ID: ${project.id || getProjectId()}`
    );


    setText(
        "projectShortDescription",

        project.business_objective ||
        project.description ||
        project.project_description ||
        "No project objective available."
    );
}


// =========================================================
// RENDER PROJECT FIELDS
// =========================================================
//
// This handles AI fields if /projects/{id} returns them.
//
// The fields match the CURRENT Project model.
//
// =========================================================

function renderProjectFields(project) {

    if (!project) {
        return;
    }


    console.log(
        "================================="
    );

    console.log(
        "CHECKING PROJECT AI FIELDS"
    );

    console.log(
        project
    );

    console.log(
        "================================="
    );


    // -----------------------------------------------------
    // DESCRIPTION
    // -----------------------------------------------------

    setContent(
        "overviewContent",
        project.overview
    );


    setContent(
        "problemStatementContent",
        project.problem_statement
    );


    setContent(
        "solutionContent",
        project.proposed_solution
    );


    setContent(
        "targetAudienceContent",
        project.target_users ||
        project.target_audience
    );


    setContent(
        "businessValueContent",
        project.business_value
    );


    setContent(
        "majorFeaturesContent",
        project.major_features ||
        project.expected_features
    );


    setContent(
        "expectedOutcomeContent",
        project.expected_outcome
    );


    // -----------------------------------------------------
    // PRD
    // -----------------------------------------------------

    setContent(
        "prdProductOverview",
        project.product_overview
    );


    setContent(
        "prdGoals",
        project.goals_and_objectives
    );


    setContent(
        "prdTargetUsers",
        project.target_users
    );


    setContent(
        "prdFunctionalRequirements",
        project.functional_requirements
    );


    setContent(
        "prdUserWorkflows",
        project.user_workflows
    );


    setContent(
        "prdBusinessRules",
        project.business_rules
    );


    setContent(
        "prdNonFunctionalRequirements",
        project.non_functional_requirements
    );


    setContent(
        "prdAssumptions",
        project.assumptions_and_dependencies
    );


    setContent(
        "prdAcceptanceCriteria",
        project.acceptance_criteria
    );


    // -----------------------------------------------------
    // SPRINT
    // -----------------------------------------------------

    setContent(
        "sprintContent",
        project.sprint_plan
    );


    // -----------------------------------------------------
    // TASKS
    // -----------------------------------------------------

    if (Array.isArray(project.tasks)) {

        displayTasks(
            project.tasks
        );
    }
}


// =========================================================
// LOAD GENERATED AI CONTENT
// =========================================================

async function loadGeneratedAIContent(
    projectId,
    accessToken
) {

    console.log("=================================");
    console.log("LOADING GENERATED AI CONTENT");
    console.log("PROJECT ID:", projectId);
    console.log("=================================");


    try {

        const response =
            await fetch(
                `${API_URL}/ai/generated/${projectId}`,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,

                        "Accept":
                            "application/json"
                    }
                }
            );


        console.log(
            "Generated AI response status:",
            response.status
        );


        const responseText =
            await response.text();


        console.log(
            "GENERATED AI RAW RESPONSE:",
            responseText
        );


        let data = null;


        try {

            data =
                responseText
                    ? JSON.parse(responseText)
                    : null;

        }
        catch (error) {

            console.error(
                "Generated AI JSON parsing error:",
                error
            );

            throw new Error(
                "Server returned invalid generated AI JSON."
            );
        }


        if (!response.ok) {

            console.error(
                "Generated AI endpoint failed:",
                data
            );

            throw new Error(
                data?.detail ||
                `Unable to load generated AI content. Status: ${response.status}`
            );
        }


        console.log("=================================");
        console.log("GENERATED AI CONTENT RECEIVED");
        console.log(data);
        console.log("=================================");


        generatedContent =
            data;


        renderAIContent(
            data
        );


    }
    catch (error) {

        console.error("=================================");
        console.error("GENERATED AI CONTENT LOAD ERROR");
        console.error(error);
        console.error("=================================");

        // Do NOT hide the project.
        //
        // This is important because the basic project
        // information can still be displayed.

        console.warn(
            "Generated AI content could not be loaded."
        );
    }
}


// =========================================================
// GENERATE ALL AI CONTENT
// =========================================================

async function generateAIContent() {

    const projectId =
        getProjectId();


    if (!projectId) {

        alert(
            "Project ID is missing."
        );

        return;
    }


    const accessToken =
        getAccessToken();


    if (!accessToken) {

        alert(
            "Authentication token is missing. Please login again."
        );

        return;
    }


    const button =
        document.getElementById(
            "generateButton"
        );


    const originalHTML =
        button
            ? button.innerHTML
            : "";


    if (button) {

        button.disabled = true;

        button.innerHTML = `

            <span
                class="
                    material-symbols-outlined
                    animate-spin
                "
            >
                progress_activity
            </span>

            Generating...

        `;
    }


    try {

        console.log("=================================");
        console.log("STARTING AI GENERATION");
        console.log("PROJECT ID:", projectId);
        console.log("=================================");


        // =================================================
        // CALL GENERATION ENDPOINT
        // =================================================

        const response =
            await fetch(
                `${API_URL}/ai/generate-all/${projectId}`,
                {
                    method: "POST",

                    headers: {
                        "Authorization":
                            `Bearer ${accessToken}`,

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    }
                }
            );


        console.log(
            "AI generation status:",
            response.status
        );


        const responseText =
            await response.text();


        console.log("=================================");
        console.log("RAW AI GENERATION RESPONSE");
        console.log(responseText);
        console.log("=================================");


        let data = null;


        try {

            data =
                responseText
                    ? JSON.parse(responseText)
                    : null;

        }
        catch (error) {

            console.error(
                "AI response JSON parsing failed:",
                error
            );

            throw new Error(
                "Server returned an invalid JSON response."
            );
        }


        console.log("=================================");
        console.log("AI GENERATION RESPONSE OBJECT");
        console.log(data);
        console.log("=================================");


        if (!response.ok) {

            throw new Error(
                data?.detail ||
                data?.message ||
                `AI generation failed with status ${response.status}`
            );
        }


        // -------------------------------------------------
        // SAVE RESPONSE
        // -------------------------------------------------

        generatedContent =
            data;


        // -------------------------------------------------
        // RENDER THE POST RESPONSE
        //
        // This is important.
        //
        // The POST endpoint already returns:
        //
        // description
        // prd
        // tasks
        // sprint_plan
        //
        // So we don't have to wait for GET to display it.
        // -------------------------------------------------

        console.log(
            "Rendering generated content from POST response."
        );


        renderAIContent(
            data
        );


        // -------------------------------------------------
        // LOAD SAVED CONTENT
        //
        // This verifies that the backend successfully
        // saved the generated content.
        // -------------------------------------------------

        console.log("=================================");
        console.log("VERIFYING SAVED AI CONTENT");
        console.log("=================================");


        await loadGeneratedAIContent(
            projectId,
            accessToken
        );


        console.log("=================================");
        console.log("AI GENERATION COMPLETE");
        console.log("=================================");


        alert(
            "Description, PRD, Tasks and Sprint Plan generated successfully."
        );


    }
    catch (error) {

        console.error("=================================");
        console.error("AI GENERATION ERROR");
        console.error(error);
        console.error("=================================");


        alert(
            error.message ||
            "Unable to generate AI content."
        );


    }
    finally {

        if (button) {

            button.disabled = false;

            button.innerHTML =
                originalHTML;
        }
    }
}


// =========================================================
// RENDER AI CONTENT
// =========================================================
//
// Expected backend response:
//
// {
//     project_id: 1,
//     description: {...},
//     prd: {...},
//     tasks: [...],
//     sprint_plan: "..."
// }
//
// =========================================================

function renderAIContent(data) {

    console.log("=================================");
    console.log("RENDERING AI CONTENT");
    console.log("=================================");


    if (!data) {

        console.warn(
            "No AI data received."
        );

        return;
    }


    console.log(
        "RAW AI DATA:",
        data
    );


    // =====================================================
    // NORMALIZE RESPONSE
    // =====================================================

    let content =
        data;


    // -----------------------------------------------------
    // Support { data: {...} }
    // -----------------------------------------------------

    if (
        data.data &&
        typeof data.data === "object" &&
        !Array.isArray(data.data)
    ) {

        content =
            data.data;
    }


    // -----------------------------------------------------
    // Support { result: {...} }
    // -----------------------------------------------------

    else if (
        data.result &&
        typeof data.result === "object" &&
        !Array.isArray(data.result)
    ) {

        content =
            data.result;
    }


    // -----------------------------------------------------
    // Support { content: {...} }
    // -----------------------------------------------------

    else if (
        data.content &&
        typeof data.content === "object" &&
        !Array.isArray(data.content)
    ) {

        content =
            data.content;
    }


    console.log(
        "NORMALIZED AI CONTENT:",
        content
    );


    // =====================================================
    // DESCRIPTION
    // =====================================================

    let description =
        content.description;


    // -----------------------------------------------------
    // Description might be JSON string
    // -----------------------------------------------------

    if (
        typeof description === "string"
    ) {

        description =
            parseJSONIfPossible(
                description
            );
    }


    if (
        !description ||
        typeof description !== "object"
    ) {

        description = {};
    }


    console.log(
        "DESCRIPTION:",
        description
    );


    setContent(
        "overviewContent",
        description.overview
    );


    setContent(
        "problemStatementContent",
        description.problem_statement
    );


    setContent(
        "solutionContent",
        description.proposed_solution
    );


    setContent(
        "targetAudienceContent",

        description.target_audience ||
        description.target_users
    );


    setContent(
        "businessValueContent",
        description.business_value
    );


    setContent(
        "majorFeaturesContent",
        description.major_features
    );


    setContent(
        "expectedOutcomeContent",
        description.expected_outcome
    );


    // =====================================================
    // PRD
    // =====================================================

    let prd =
        content.prd;


    // -----------------------------------------------------
    // PRD might be JSON string
    // -----------------------------------------------------

    if (
        typeof prd === "string"
    ) {

        prd =
            parseJSONIfPossible(
                prd
            );
    }


    if (
        !prd ||
        typeof prd !== "object"
    ) {

        prd = {};
    }


    console.log(
        "PRD:",
        prd
    );


    setContent(
        "prdProductOverview",
        prd.product_overview
    );


    setContent(
        "prdGoals",
        prd.goals_and_objectives
    );


    setContent(
        "prdTargetUsers",
        prd.target_users
    );


    setContent(
        "prdFunctionalRequirements",
        prd.functional_requirements
    );


    setContent(
        "prdUserWorkflows",
        prd.user_workflows
    );


    setContent(
        "prdBusinessRules",
        prd.business_rules
    );


    setContent(
        "prdNonFunctionalRequirements",
        prd.non_functional_requirements
    );


    setContent(
        "prdAssumptions",
        prd.assumptions_and_dependencies
    );


    setContent(
        "prdAcceptanceCriteria",
        prd.acceptance_criteria
    );


    // =====================================================
    // TASKS
    // =====================================================

    let tasks =
        content.tasks;


    // -----------------------------------------------------
    // Tasks might be JSON string
    // -----------------------------------------------------

    if (
        typeof tasks === "string"
    ) {

        tasks =
            parseJSONIfPossible(
                tasks
            );
    }


    if (
        !Array.isArray(tasks)
    ) {

        tasks = [];
    }


    console.log(
        "TASKS:",
        tasks
    );


    displayTasks(
        tasks
    );


    // =====================================================
    // SPRINT PLAN
    // =====================================================

    let sprintPlan =
        content.sprint_plan ||
        content.sprint ||
        content.sprintPlan ||
        "";


    // -----------------------------------------------------
    // Sprint might accidentally be object
    // -----------------------------------------------------

    if (
        typeof sprintPlan === "object" &&
        sprintPlan !== null
    ) {

        sprintPlan =
            JSON.stringify(
                sprintPlan,
                null,
                2
            );
    }


    console.log(
        "SPRINT PLAN:",
        sprintPlan
    );


    setContent(
        "sprintContent",
        sprintPlan
    );


    console.log("=================================");
    console.log("AI CONTENT RENDERING COMPLETE");
    console.log("=================================");
}


// =========================================================
// PARSE JSON SAFELY
// =========================================================

function parseJSONIfPossible(value) {

    if (
        typeof value !== "string"
    ) {

        return value;
    }


    try {

        return JSON.parse(
            value
        );

    }
    catch (error) {

        console.warn(
            "Value is not valid JSON:",
            value
        );

        return value;
    }
}


// =========================================================
// SET CONTENT
// =========================================================

function setContent(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {

        console.warn(
            "Element not found:",
            elementId
        );

        return;
    }


    // -----------------------------------------------------
    // EMPTY VALUE
    // -----------------------------------------------------

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        element.innerHTML = `
            <div class="empty-content">
                Content not generated yet.
            </div>
        `;

        return;
    }


    // -----------------------------------------------------
    // ARRAY
    // -----------------------------------------------------

    if (
        Array.isArray(value)
    ) {

        element.innerHTML = `

            <ul class="list-disc pl-6 space-y-2">

                ${value
                    .map(
                        item => {

                            if (
                                typeof item === "object" &&
                                item !== null
                            ) {

                                return `
                                    <li>
                                        ${escapeHtml(
                                            JSON.stringify(
                                                item,
                                                null,
                                                2
                                            )
                                        )}
                                    </li>
                                `;
                            }


                            return `
                                <li>
                                    ${escapeHtml(
                                        item
                                    )}
                                </li>
                            `;
                        }
                    )
                    .join("")
                }

            </ul>
        `;

        return;
    }


    // -----------------------------------------------------
    // OBJECT
    // -----------------------------------------------------

    if (
        typeof value === "object"
    ) {

        element.innerHTML = `

            <pre
                class="
                    whitespace-pre-wrap
                    text-sm
                "
            >${escapeHtml(
                JSON.stringify(
                    value,
                    null,
                    2
                )
            )}</pre>

        `;

        return;
    }


    // -----------------------------------------------------
    // STRING
    // -----------------------------------------------------

    element.innerHTML =
        escapeHtml(
            String(value)
        )
        .replace(
            /\r?\n/g,
            "<br>"
        );
}


// =========================================================
// TASKS
// =========================================================

function displayTasks(tasks) {

    const container =
        document.getElementById(
            "tasksContainer"
        );


    const noTasks =
        document.getElementById(
            "noTasks"
        );


    if (!container) {

        console.warn(
            "tasksContainer element not found."
        );

        return;
    }


    container.innerHTML =
        "";


    if (
        !Array.isArray(tasks) ||
        tasks.length === 0
    ) {

        if (noTasks) {

            noTasks.classList.remove(
                "hidden"
            );
        }

        return;
    }


    if (noTasks) {

        noTasks.classList.add(
            "hidden"
        );
    }


    tasks.forEach(
        function (
            task,
            index
        ) {

            const card =
                createTaskCard(
                    task,
                    index
                );


            container.appendChild(
                card
            );
        }
    );
}


// =========================================================
// CREATE TASK CARD
// =========================================================

function createTaskCard(
    task,
    index
) {

    const card =
        document.createElement(
            "div"
        );


    card.className =
        "bg-surface-container-lowest " +
        "border border-outline-variant " +
        "rounded-xl p-6 " +
        "hover:shadow-md transition";


    const title =
        task.task_title ||
        task.title ||
        task.task_name ||
        task.name ||
        `Task ${index + 1}`;


    const description =
        task.description ||
        "";


    const status =
        task.status ||
        "Todo";


    const priority =
        task.priority ||
        "Medium";


    const module =
        task.module ||
        task.category ||
        "General";


    const complexity =
        task.estimated_complexity ||
        task.complexity ||
        task.complexity_score ||
        "-";


    const owner =
        task.owner_role ||
        task.assignee ||
        task.owner ||
        "Unassigned";


    let criteria =
        task.acceptance_criteria ||
        [];


    // -----------------------------------------------------
    // NORMALIZE ACCEPTANCE CRITERIA
    // -----------------------------------------------------

    if (
        typeof criteria === "string"
    ) {

        criteria =
            parseJSONIfPossible(
                criteria
            );
    }


    if (
        !Array.isArray(criteria)
    ) {

        criteria =
            criteria
                ? [criteria]
                : [];
    }


    card.innerHTML = `

        <div class="
            flex flex-col
            lg:flex-row
            lg:items-start
            lg:justify-between
            gap-4
        ">

            <div class="flex gap-4">

                <button
                    type="button"
                    class="
                        task-check
                        w-6 h-6
                        rounded-md
                        border
                        border-outline-variant
                        flex
                        items-center
                        justify-center
                        flex-shrink-0
                    "
                >

                    <span
                        class="
                            material-symbols-outlined
                            text-sm
                            hidden
                        "
                    >
                        check
                    </span>

                </button>


                <div>

                    <h3
                        class="
                            text-xl
                            font-semibold
                            font-headline
                        "
                    >
                        ${escapeHtml(title)}
                    </h3>


                    <p
                        class="
                            mt-2
                            text-sm
                            text-on-surface-variant
                        "
                    >
                        ${escapeHtml(description)}
                    </p>


                    <div
                        class="
                            flex
                            flex-wrap
                            gap-2
                            mt-4
                        "
                    >

                        <span
                            class="
                                px-3 py-1
                                rounded-full
                                bg-secondary-container
                                text-primary
                                text-xs
                                font-semibold
                            "
                        >
                            ${escapeHtml(module)}
                        </span>


                        <span
                            class="
                                px-3 py-1
                                rounded-full
                                bg-surface-container-high
                                text-xs
                            "
                        >
                            ${escapeHtml(status)}
                        </span>


                        <span
                            class="
                                px-3 py-1
                                rounded-full
                                bg-surface-container-high
                                text-xs
                            "
                        >
                            ${escapeHtml(priority)}
                        </span>

                    </div>

                </div>

            </div>


            <div
                class="
                    text-sm
                    text-on-surface-variant
                "
            >

                <div>
                    <strong>Owner:</strong>
                    ${escapeHtml(owner)}
                </div>

                <div class="mt-1">
                    <strong>Complexity:</strong>
                    ${escapeHtml(complexity)}
                </div>

            </div>

        </div>


        ${
            criteria.length > 0

                ? `

                <div
                    class="
                        mt-6
                        pt-5
                        border-t
                        border-outline-variant
                    "
                >

                    <h4
                        class="
                            font-semibold
                            flex
                            items-center
                            gap-2
                            mb-3
                        "
                    >

                        <span
                            class="
                                material-symbols-outlined
                                text-primary
                            "
                        >
                            rule
                        </span>

                        Acceptance Criteria

                    </h4>


                    <ul
                        class="space-y-2"
                    >

                        ${criteria
                            .map(
                                criterion => {

                                    if (
                                        typeof criterion === "object" &&
                                        criterion !== null
                                    ) {

                                        criterion =
                                            JSON.stringify(
                                                criterion
                                            );
                                    }


                                    return `

                                        <li
                                            class="
                                                flex
                                                items-start
                                                gap-2
                                                text-sm
                                                text-on-surface-variant
                                            "
                                        >

                                            <span
                                                class="
                                                    material-symbols-outlined
                                                    text-primary
                                                    text-base
                                                "
                                            >
                                                radio_button_unchecked
                                            </span>

                                            <span>
                                                ${escapeHtml(
                                                    criterion
                                                )}
                                            </span>

                                        </li>

                                    `;
                                }
                            )
                            .join("")
                        }

                    </ul>

                </div>

                `

                : ""

        }

    `;


    // =====================================================
    // TASK CHECKBOX
    // =====================================================

    const checkbox =
        card.querySelector(
            ".task-check"
        );


    if (checkbox) {

        checkbox.addEventListener(
            "click",
            function () {

                checkbox
                    .classList
                    .toggle(
                        "bg-primary"
                    );


                checkbox
                    .classList
                    .toggle(
                        "text-white"
                    );


                const icon =
                    checkbox.querySelector(
                        "span"
                    );


                if (icon) {

                    icon
                        .classList
                        .toggle(
                            "hidden"
                        );
                }
            }
        );
    }


    return card;
}


// =========================================================
// BUTTONS
// =========================================================

function setupButtons() {

    // -----------------------------------------------------
    // GENERATE BUTTON
    // -----------------------------------------------------

    const generateButton =
        document.getElementById(
            "generateButton"
        );


    if (generateButton) {

        generateButton.addEventListener(
            "click",
            generateAIContent
        );

    }
    else {

        console.warn(
            "Generate button not found."
        );
    }


    // -----------------------------------------------------
    // EDIT BUTTONS
    // -----------------------------------------------------

    const editButtons =
        document.querySelectorAll(
            ".edit-button"
        );


    editButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    alert(
                        "Editing functionality will be added next."
                    );
                }
            );
        }
    );
}


// =========================================================
// NAVIGATION
// =========================================================

function setupNavigation() {

    // -----------------------------------------------------
    // DASHBOARD LINKS
    // -----------------------------------------------------

    const projectLinks =
        document.querySelectorAll(
            'a[href="dashboard.html"]'
        );


    projectLinks.forEach(
        function (link) {

            link.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    window.location.href =
                        "dashboard.html";
                }
            );
        }
    );


    // -----------------------------------------------------
    // NEW PROJECT BUTTON
    // -----------------------------------------------------

    const newProjectButton =
        document.getElementById(
            "newProjectButton"
        );


    if (newProjectButton) {

        newProjectButton.addEventListener(
            "click",
            function () {

                window.location.href =
                    "create-project.html";
            }
        );
    }


    // -----------------------------------------------------
    // TOP NEW PROJECT BUTTON
    // -----------------------------------------------------

    const topNewProjectButton =
        document.getElementById(
            "topNewProjectButton"
        );


    if (topNewProjectButton) {

        topNewProjectButton.addEventListener(
            "click",
            function () {

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

    const tabButtons =
        document.querySelectorAll(
            ".tab-button"
        );


    const tabContents = {

        description:
            document.getElementById(
                "descriptionTab"
            ),

        prd:
            document.getElementById(
                "prdTab"
            ),

        tasks:
            document.getElementById(
                "tasksTab"
            ),

        sprint:
            document.getElementById(
                "sprintTab"
            )
    };


    tabButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    const selectedTab =
                        button.dataset.tab;


                    console.log(
                        "Selected tab:",
                        selectedTab
                    );


                    // -------------------------------------------------
                    // HIDE ALL TABS
                    // -------------------------------------------------

                    Object.values(
                        tabContents
                    ).forEach(
                        function (content) {

                            if (content) {

                                content.classList.add(
                                    "hidden"
                                );
                            }
                        }
                    );


                    // -------------------------------------------------
                    // SHOW SELECTED TAB
                    // -------------------------------------------------

                    if (
                        tabContents[selectedTab]
                    ) {

                        tabContents[selectedTab]
                            .classList
                            .remove(
                                "hidden"
                            );

                    }
                    else {

                        console.warn(
                            "Tab content not found:",
                            selectedTab
                        );
                    }


                    // -------------------------------------------------
                    // RESET BUTTONS
                    // -------------------------------------------------

                    tabButtons.forEach(
                        function (btn) {

                            btn.classList.remove(
                                "border-primary",
                                "text-primary",
                                "font-semibold"
                            );


                            btn.classList.add(
                                "border-transparent",
                                "text-on-surface-variant"
                            );
                        }
                    );


                    // -------------------------------------------------
                    // ACTIVATE SELECTED BUTTON
                    // -------------------------------------------------

                    button.classList.remove(
                        "border-transparent",
                        "text-on-surface-variant"
                    );


                    button.classList.add(
                        "border-primary",
                        "text-primary",
                        "font-semibold"
                    );
                }
            );
        }
    );
}


// =========================================================
// SAFE HTML
// =========================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}


// =========================================================
// SET TEXT
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

        console.warn(
            "Text element not found:",
            elementId
        );

        return;
    }


    element.textContent =
        value !== null &&
        value !== undefined &&
        value !== ""
            ? String(value)
            : "Not available.";
}


// =========================================================
// ERROR STATE
// =========================================================

function showError(message) {

    document
        .getElementById(
            "loadingState"
        )
        ?.classList.add(
            "hidden"
        );


    document
        .getElementById(
            "projectContent"
        )
        ?.classList.add(
            "hidden"
        );


    document
        .getElementById(
            "errorState"
        )
        ?.classList.remove(
            "hidden"
        );


    const errorMessage =
        document.getElementById(
            "errorMessage"
        );


    if (errorMessage) {

        errorMessage.textContent =
            message;
    }
}
