console.log("=================================");
console.log("DASHBOARD JS LOADED");
console.log("=================================");

const API_URL = "http://127.0.0.1:8000";

// =========================================================
// GLOBAL STATE
// =========================================================

let allProjects = [];
let currentView = "grid";


// =========================================================
// PAGE LOAD
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("Dashboard DOM loaded.");

    // Authentication
    if (!checkAuthentication()) {
        return;
    }

    // Buttons
    setupNewProjectButtons();

    // Navigation
    setupNavigation();

    // Search
    setupSearch();

    // Grid / List
    setupViewToggle();

    // User profile
    setupUserProfile();

    // Load projects
    loadProjects();

});


// =========================================================
// CHECK AUTHENTICATION
// =========================================================

function checkAuthentication() {

    const userId =
        localStorage.getItem("user_id");

    const accessToken =
        localStorage.getItem("access_token");


    console.log("USER ID:", userId);

    console.log(
        "ACCESS TOKEN:",
        accessToken ? "EXISTS" : "MISSING"
    );


    if (!userId || !accessToken) {

        console.error(
            "Authentication information is missing."
        );

        window.location.href =
            "../index.html";

        return false;
    }


    console.log(
        "User authentication verified."
    );

    return true;
}


// =========================================================
// NEW PROJECT BUTTON
// =========================================================

function setupNewProjectButtons() {

    const newProjectBtn =
        document.getElementById("newProjectBtn");


    if (newProjectBtn) {

        newProjectBtn.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                console.log(
                    "New Project button clicked."
                );

                window.location.href =
                    "create-project.html";

            }
        );

    }

}


// =========================================================
// NAVIGATION
// =========================================================

function setupNavigation() {

    const dashboardLink =
        document.getElementById("dashboardLink");

    if (dashboardLink) {

        dashboardLink.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                window.location.href =
                    "dashboard.html";

            }
        );

    }


    const projectsLink =
        document.getElementById("projectsLink");

    if (projectsLink) {

        projectsLink.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                window.location.href =
                    "dashboard.html";

            }
        );

    }

}


// =========================================================
// LOAD PROJECTS
// =========================================================

async function loadProjects() {

    const userId =
        localStorage.getItem("user_id");

    const accessToken =
        localStorage.getItem("access_token");


    console.log("=================================");
    console.log("LOADING DASHBOARD PROJECTS");
    console.log("USER ID:", userId);
    console.log(
        "ACCESS TOKEN:",
        accessToken ? "EXISTS" : "MISSING"
    );
    console.log("=================================");


    if (!userId || !accessToken) {

        console.error(
            "User is not authenticated."
        );

        window.location.href =
            "../index.html";

        return;
    }


    try {

        const response = await fetch(
            `${API_URL}/projects/`,
            {
                method: "GET",

                headers: {
                    "Authorization": `Bearer ${accessToken}`,
                    "Content-Type": "application/json"
                }
            }
        );


        console.log(
            "Project API status:",
            response.status
        );


        // -------------------------------------------------
        // AUTH ERROR
        // -------------------------------------------------

        if (response.status === 401) {

            console.error(
                "Authentication failed."
            );

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "user"
            );

            localStorage.removeItem(
                "user_id"
            );

            window.location.href =
                "../index.html";

            return;
        }


        // -------------------------------------------------
        // OTHER API ERROR
        // -------------------------------------------------

        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Project API failed:",
                response.status
            );

            console.error(
                "Backend error:",
                errorText
            );

            showProjectError(
                `Unable to load projects. Server returned ${response.status}.`
            );

            return;
        }


        // -------------------------------------------------
        // GET PROJECTS
        // -------------------------------------------------

        const projects =
            await response.json();


        console.log(
            "Projects received:",
            projects
        );


        // -------------------------------------------------
        // SAVE ORIGINAL PROJECT LIST
        // -------------------------------------------------

        if (Array.isArray(projects)) {

            allProjects = projects;

        } else if (
            projects &&
            Array.isArray(projects.projects)
        ) {

            allProjects =
                projects.projects;

        } else {

            allProjects = [];

        }


        console.log(
            "Total projects:",
            allProjects.length
        );


        // -------------------------------------------------
        // RENDER
        // -------------------------------------------------

        renderProjects(allProjects);

    }
    catch (error) {

        console.error(
            "PROJECT LOAD ERROR:",
            error
        );

        showProjectError(
            "Unable to connect to the backend server."
        );

    }

}

// =========================================================
// DELETE PROJECT
// =========================================================

async function deleteProject(projectId, projectName) {

    console.log("=================================");
    console.log("DELETE PROJECT");
    console.log("PROJECT ID:", projectId);
    console.log("PROJECT NAME:", projectName);
    console.log("=================================");

    // -----------------------------------------------------
    // CONFIRMATION
    // -----------------------------------------------------

    const confirmed = window.confirm(
        `Are you sure you want to delete "${projectName}"?\n\n` +
        `This will permanently delete the project, ` +
        `requirements, tasks, conversations and messages.\n\n` +
        `This action cannot be undone.`
    );

    if (!confirmed) {

        console.log(
            "Project deletion cancelled."
        );

        return;
    }


    // -----------------------------------------------------
    // AUTHENTICATION
    // -----------------------------------------------------

    const accessToken =
        localStorage.getItem("access_token");


    if (!accessToken) {

        console.error(
            "Access token not found."
        );

        window.location.href =
            "../index.html";

        return;
    }


    try {

        // -------------------------------------------------
        // DELETE REQUEST
        // -------------------------------------------------

        const response = await fetch(
            `${API_URL}/projects/${projectId}`,
            {
                method: "DELETE",

                headers: {
                    "Authorization": `Bearer ${accessToken}`,
                    "Accept": "application/json"
                }
            }
        );


        console.log(
            "Delete API status:",
            response.status
        );


        // -------------------------------------------------
        // AUTH ERROR
        // -------------------------------------------------

        if (response.status === 401) {

            console.error(
                "Authentication failed."
            );

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "user"
            );

            localStorage.removeItem(
                "user_id"
            );

            window.location.href =
                "../index.html";

            return;
        }


        // -------------------------------------------------
        // OTHER ERROR
        // -------------------------------------------------

        if (!response.ok) {

            const errorData =
                await response.json()
                    .catch(() => ({}));


            console.error(
                "Delete project failed:",
                errorData
            );

            showNotification(
                errorData.detail ||
                "Unable to delete the project.",
                "error"
            );
            

            return;
        }


        // -------------------------------------------------
        // SUCCESS
        // -------------------------------------------------

        const data =
            await response.json();


        console.log(
            "Project deleted successfully:",
            data
        );


        // -------------------------------------------------
        // CLEAR SELECTED PROJECT
        // -------------------------------------------------

        const selectedProjectId =
            localStorage.getItem(
                "selected_project_id"
            );


        if (
            selectedProjectId ===
            String(projectId)
        ) {

            localStorage.removeItem(
                "selected_project_id"
            );

            localStorage.removeItem(
                "selected_project_name"
            );

            localStorage.removeItem(
                "agent_thread_id"
            );

            console.log(
                "Selected project information cleared."
            );
        }


        // -------------------------------------------------
        // REMOVE FROM LOCAL PROJECT LIST
        // -------------------------------------------------

        allProjects =
            allProjects.filter(
                function (project) {

                    const id =
                        project.id ??
                        project.project_id;

                    return String(id) !==
                        String(projectId);
                }
            );


        // -------------------------------------------------
        // REFRESH DISPLAY
        // -------------------------------------------------

        renderCurrentProjects();

            showNotification(
                `"${projectName}" was deleted successfully.`
            );
        console.log(
            "Dashboard updated after deletion."
        );

    }
    catch (error) {

        console.error(
            "DELETE PROJECT ERROR:",
            error
        );

        showNotification(
            "Unable to connect to the backend server.",
            "error"
        );

    }

}

// =========================================================
// SHOW NOTIFICATION
// =========================================================

function showNotification(message, type = "success") {

    // Remove existing notification
    const existingNotification =
        document.getElementById("dashboardNotification");

    if (existingNotification) {
        existingNotification.remove();
    }


    const notification =
        document.createElement("div");

    notification.id =
        "dashboardNotification";


    const isSuccess =
        type === "success";


    notification.className = `
        fixed
        top-6
        right-6
        z-[9999]
        flex
        items-center
        gap-3
        px-5
        py-4
        rounded-xl
        shadow-lg
        border
        backdrop-blur-sm
        transition-all
        duration-300
        translate-x-0
        opacity-100
        ${isSuccess
            ? "bg-green-50 border-green-200 text-green-800"
            : "bg-red-50 border-red-200 text-red-800"
        }
    `;


    notification.innerHTML = `

        <div class="
            w-9
            h-9
            rounded-full
            flex
            items-center
            justify-center
            ${isSuccess
                ? "bg-green-100"
                : "bg-red-100"
            }
        ">

            <span class="
                material-symbols-outlined
                text-[20px]
                ${isSuccess
                    ? "text-green-600"
                    : "text-red-600"
                }
            ">
                ${isSuccess
                    ? "check_circle"
                    : "error"
                }
            </span>

        </div>


        <div class="flex flex-col">

            <span class="
                text-[14px]
                font-semibold
            ">
                ${isSuccess
                    ? "Success"
                    : "Something went wrong"
                }
            </span>

            <span class="
                text-[13px]
                opacity-80
            ">
                ${escapeHtml(message)}
            </span>

        </div>


        <button
            type="button"
            class="
                ml-2
                opacity-60
                hover:opacity-100
                transition-opacity
            "
            title="Close"
        >
            <span class="
                material-symbols-outlined
                text-[18px]
            ">
                close
            </span>
        </button>

    `;


    document.body.appendChild(
        notification
    );


    // -----------------------------------------------------
    // CLOSE BUTTON
    // -----------------------------------------------------

    const closeButton =
        notification.querySelector("button");


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            function () {

                notification.remove();

            }
        );

    }


    // -----------------------------------------------------
    // AUTO REMOVE
    // -----------------------------------------------------

    setTimeout(
        function () {

            if (notification) {
                notification.remove();
            }

        },
        4000
    );

}
// =========================================================
// SEARCH
// =========================================================

function setupSearch() {

    const projectSearch =
        document.getElementById("projectSearch");


    if (!projectSearch) {

        console.warn(
            "Project search input not found."
        );

        return;
    }


    projectSearch.addEventListener(
        "input",
        function () {

            const searchText =
                this.value
                    .trim()
                    .toLowerCase();


            console.log(
                "Searching projects:",
                searchText
            );


            // Search ORIGINAL project list
            const filteredProjects =
                allProjects.filter(
                    function (project) {

                        const projectName =
                            project.project_name ||
                            project.name ||
                            "";


                        return projectName
                            .toLowerCase()
                            .includes(searchText);

                    }
                );


            renderProjects(
                filteredProjects,
                searchText
            );

        }
    );

}


// =========================================================
// GRID / LIST VIEW
// =========================================================

function setupViewToggle() {

    const gridViewBtn =
        document.getElementById("gridViewBtn");

    const listViewBtn =
        document.getElementById("listViewBtn");


    if (!gridViewBtn || !listViewBtn) {

        console.warn(
            "Grid/List buttons not found."
        );

        return;
    }


    // -----------------------------------------------------
    // GRID
    // -----------------------------------------------------

    gridViewBtn.addEventListener(
        "click",
        function () {

            currentView = "grid";

            console.log(
                "View changed to GRID."
            );

            updateViewButtons();

            renderCurrentProjects();
                       

        }
    );


    // -----------------------------------------------------
    // LIST
    // -----------------------------------------------------

    listViewBtn.addEventListener(
        "click",
        function () {

            currentView = "list";

            console.log(
                "View changed to LIST."
            );

            updateViewButtons();

            renderCurrentProjects();

        }
    );


    // Initial state
    updateViewButtons();

}


// =========================================================
// RENDER CURRENT PROJECTS
// =========================================================

function renderCurrentProjects() {

    const projectSearch =
        document.getElementById("projectSearch");


    const searchText =
        projectSearch
            ? projectSearch.value
                .trim()
                .toLowerCase()
            : "";


    const filteredProjects =
        allProjects.filter(
            function (project) {

                const projectName =
                    project.project_name ||
                    project.name ||
                    "";


                return projectName
                    .toLowerCase()
                    .includes(searchText);

            }
        );


    renderProjects(
        filteredProjects,
        searchText
    );

}


// =========================================================
// UPDATE GRID / LIST BUTTONS
// =========================================================

function updateViewButtons() {

    const gridViewBtn =
        document.getElementById("gridViewBtn");

    const listViewBtn =
        document.getElementById("listViewBtn");


    if (!gridViewBtn || !listViewBtn) {
        return;
    }


    if (currentView === "grid") {

        gridViewBtn.className =
            `
            bg-surface-container-low
            text-on-surface
            px-3
            py-1.5
            rounded-md
            font-label-sm
            text-label-sm
            shadow-sm
            border
            border-outline-variant/50
            flex
            items-center
            gap-1.5
            transition-colors
            `;


        listViewBtn.className =
            `
            text-on-surface-variant
            hover:bg-surface-container-low
            px-3
            py-1.5
            rounded-md
            font-label-sm
            text-label-sm
            transition-colors
            flex
            items-center
            gap-1.5
            `;

    } else {

        listViewBtn.className =
            `
            bg-surface-container-low
            text-on-surface
            px-3
            py-1.5
            rounded-md
            font-label-sm
            text-label-sm
            shadow-sm
            border
            border-outline-variant/50
            flex
            items-center
            gap-1.5
            transition-colors
            `;


        gridViewBtn.className =
            `
            text-on-surface-variant
            hover:bg-surface-container-low
            px-3
            py-1.5
            rounded-md
            font-label-sm
            text-label-sm
            transition-colors
            flex
            items-center
            gap-1.5
            `;

    }

}


// =========================================================
// SHOW PROJECT ERROR
// =========================================================

function showProjectError(message) {

    const projectGrid =
        document.getElementById(
            "projectGrid"
        );


    if (!projectGrid) {

        console.error(
            "projectGrid not found."
        );

        return;
    }


    projectGrid.innerHTML = `

        <div class="
            col-span-full
            flex
            flex-col
            items-center
            justify-center
            py-16
            text-center
        ">

            <div class="
                w-16
                h-16
                rounded-full
                bg-red-50
                text-red-600
                flex
                items-center
                justify-center
                mb-4
            ">

                <span class="
                    material-symbols-outlined
                    text-[32px]
                ">
                    error_outline
                </span>

            </div>

            <h3 class="
                font-headline-md
                text-[20px]
                text-on-surface
                mb-2
            ">
                Unable to Load Projects
            </h3>

            <p class="
                font-body-sm
                text-on-surface-variant
            ">
                ${escapeHtml(message)}
            </p>

            <button
                id="retryProjectsBtn"
                type="button"
                class="
                    mt-4
                    bg-primary
                    text-white
                    px-5
                    py-2
                    rounded-lg
                    hover:opacity-90
                "
            >
                Retry
            </button>

        </div>
    `;


    const retryButton =
        document.getElementById(
            "retryProjectsBtn"
        );


    if (retryButton) {

        retryButton.addEventListener(
            "click",
            function () {

                loadProjects();

            }
        );

    }

}


// =========================================================
// RENDER PROJECTS
// =========================================================

function renderProjects(
    projects,
    searchText = ""
) {

    const projectGrid =
        document.getElementById(
            "projectGrid"
        );


    if (!projectGrid) {

        console.error(
            "projectGrid not found!"
        );

        return;
    }


    // Remove existing cards
    projectGrid.innerHTML = "";


    // -----------------------------------------------------
    // SEARCH FOUND NOTHING
    // -----------------------------------------------------

    if (
        searchText &&
        projects.length === 0
    ) {

        projectGrid.innerHTML = `

            <div class="
                col-span-full
                flex
                flex-col
                items-center
                justify-center
                py-16
                text-center
            ">

                <span class="
                    material-symbols-outlined
                    text-[48px]
                    text-on-surface-variant
                    mb-3
                ">
                    search_off
                </span>

                <h3 class="
                    font-headline-md
                    text-[20px]
                    text-on-surface
                    mb-2
                ">
                    No Projects Found
                </h3>

                <p class="
                    font-body-sm
                    text-on-surface-variant
                ">
                    No project matches "${escapeHtml(searchText)}".
                </p>

            </div>

        `;

        return;
    }


    // -----------------------------------------------------
    // NO PROJECTS AT ALL
    // -----------------------------------------------------

    if (
        !projects ||
        !Array.isArray(projects) ||
        projects.length === 0
    ) {

        console.log(
            "No projects found."
        );

        addCreateProjectCard();

        return;
    }


    console.log(
        `Rendering ${projects.length} project(s) in ${currentView} view.`
    );


    // -----------------------------------------------------
    // PROJECT CARDS
    // -----------------------------------------------------

    projects.forEach(
        function (project) {

            const card =
                createProjectCard(project);


            if (card) {

                projectGrid.appendChild(
                    card
                );

            }

        }
    );


    // -----------------------------------------------------
    // CREATE PROJECT CARD
    // -----------------------------------------------------

    addCreateProjectCard();

}


// =========================================================
// CREATE PROJECT CARD
// =========================================================

function createProjectCard(project) {

    const projectId =
        project.id ??
        project.project_id;


    if (
        projectId === null ||
        projectId === undefined ||
        projectId === ""
    ) {

        console.error(
            "Project ID missing:",
            project
        );

        return null;
    }


    const article =
        document.createElement("article");


    // =====================================================
    // GRID STYLE
    // =====================================================

    if (currentView === "grid") {

        article.className = `
            project-card
            bg-surface-container-lowest
            rounded-[12px]
            border
            border-outline-variant/60
            shadow-[0px_4px_12px_rgba(15,23,42,0.03)]
            hover:shadow-[0px_8px_24px_rgba(15,23,42,0.06)]
            hover:border-primary/30
            transition-all
            duration-300
            p-6
            flex
            flex-col
            group
            relative
            overflow-hidden
            cursor-pointer
        `;

    }


    // =====================================================
    // LIST STYLE
    // =====================================================

    else {

        article.className = `
            project-card
            bg-surface-container-lowest
            rounded-[12px]
            border
            border-outline-variant/60
            shadow-sm
            hover:shadow-md
            hover:border-primary/30
            transition-all
            duration-300
            p-5
            flex
            items-center
            gap-5
            group
            relative
            overflow-hidden
            cursor-pointer
        `;

    }


    // =====================================================
    // PROJECT DATA
    // =====================================================

    const projectName =
        project.project_name ||
        project.name ||
        "Untitled Project";


    const category =
        project.category ||
        "General";


    const description =
        project.business_objective ||
        project.description ||
        "No project description available.";


    const timeline =
        project.timeline ||
        "Not specified";


    // =====================================================
    // GRID CARD HTML
    // =====================================================

    if (currentView === "grid") {

        article.innerHTML = `

            <div class="
                flex
                justify-between
                items-start
                mb-4
            ">

                <div class="
                    w-10
                    h-10
                    rounded-lg
                    bg-blue-50
                    text-blue-600
                    flex
                    items-center
                    justify-center
                ">

                    <span class="
                        material-symbols-outlined
                    ">
                        folder
                    </span>

                </div>


                <span class="
                    bg-blue-50
                    text-blue-700
                    px-2.5
                    py-1
                    rounded-full
                    text-[11px]
                    uppercase
                ">
                    ${escapeHtml(category)}
                </span>

            </div>


            <h3 class="
                font-headline-md
                text-[20px]
                text-on-surface
                mb-2
            ">
                ${escapeHtml(projectName)}
            </h3>


            <p class="
                font-body-sm
                text-on-surface-variant
                mb-6
                line-clamp-2
            ">
                ${escapeHtml(description)}
            </p>


            <div class="
    mt-auto
    pt-4
    border-t
    border-outline-variant/40
    flex
    items-center
    justify-between
    gap-3
">

    <span class="
        font-body-sm
        text-[12px]
        text-on-surface-variant
        truncate
    ">
        Timeline:
        ${escapeHtml(timeline)}
    </span>

    <button
        type="button"
        class="
            delete-project-btn
            flex
            items-center
            gap-1
            px-3
            py-1.5
            rounded-lg
            text-error
            hover:bg-error-container
            transition-colors
            text-[12px]
            font-semibold
            flex-shrink-0
        "
        title="Delete project"
    >
        <span class="
            material-symbols-outlined
            text-[17px]
        ">
            delete
        </span>
        Delete
    </button>

</div>
        `;

    }


    // =====================================================
    // LIST CARD HTML
    // =====================================================

    else {

        article.innerHTML = `

            <div class="
                w-11
                h-11
                flex-shrink-0
                rounded-lg
                bg-blue-50
                text-blue-600
                flex
                items-center
                justify-center
            ">

                <span class="
                    material-symbols-outlined
                ">
                    folder
                </span>

            </div>


            <div class="
                flex-1
                min-w-0
            ">

                <div class="
                    flex
                    items-center
                    gap-3
                    mb-1
                ">

                    <h3 class="
                        font-headline-md
                        text-[18px]
                        text-on-surface
                        font-semibold
                        truncate
                    ">
                        ${escapeHtml(projectName)}
                    </h3>


                    <span class="
                        flex-shrink-0
                        bg-blue-50
                        text-blue-700
                        px-2.5
                        py-1
                        rounded-full
                        text-[10px]
                        uppercase
                    ">
                        ${escapeHtml(category)}
                    </span>

                </div>


                <p class="
                    font-body-sm
                    text-on-surface-variant
                    truncate
                ">
                    ${escapeHtml(description)}
                </p>

            </div>


            <div class="
                hidden
                sm:block
                flex-shrink-0
                text-right
            ">

                <p class="
                    text-[11px]
                    text-on-surface-variant
                    mb-1
                ">
                    Timeline
                </p>

                <p class="
                    font-label-sm
                    text-label-sm
                    text-on-surface
                ">
                    ${escapeHtml(timeline)}
                </p>

            </div>


            <span class="
                material-symbols-outlined
                text-on-surface-variant
                group-hover:text-primary
                transition-colors
            ">
                chevron_right
            </span>

        `;

    }

// =====================================================
// DELETE BUTTON
// =====================================================

const deleteButton =
    article.querySelector(
        ".delete-project-btn"
    );


if (deleteButton) {

    deleteButton.addEventListener(
        "click",
        async function (event) {

            // IMPORTANT:
            // Prevent the card click from opening
            // the project details page.

            event.preventDefault();
            event.stopPropagation();

            await deleteProject(
                projectId,
                projectName
            );

        }
    );

}
    // =====================================================
    // CARD CLICK
    // =====================================================

    article.addEventListener(
        "click",
        function () {

            console.log(
                "================================="
            );

            console.log(
                "PROJECT CARD CLICKED"
            );

            console.log(
                "PROJECT ID:",
                projectId
            );

            console.log(
                "PROJECT NAME:",
                projectName
            );

            console.log(
                "================================="
            );


            localStorage.setItem(
                "selected_project_id",
                String(projectId)
            );


            const detailsUrl =
                `project-details.html?id=${encodeURIComponent(projectId)}`;


            console.log(
                "Redirecting to:",
                detailsUrl
            );


            window.location.href =
                detailsUrl;

        }
    );


    return article;

}


// =========================================================
// CREATE NEW PROJECT CARD
// =========================================================

function addCreateProjectCard() {

    const projectGrid =
        document.getElementById(
            "projectGrid"
        );


    if (!projectGrid) {
        return;
    }


    const card =
        document.createElement("article");


    card.className = `
        bg-surface-container-low
        border-2
        border-dashed
        border-outline-variant/50
        rounded-[12px]
        hover:bg-surface-container
        hover:border-primary/40
        transition-all
        duration-300
        flex
        flex-col
        items-center
        justify-center
        text-center
        p-8
        group
        cursor-pointer
        min-h-[280px]
    `;


    card.innerHTML = `

        <div class="
            w-14
            h-14
            rounded-full
            bg-primary/10
            text-primary
            flex
            items-center
            justify-center
            mb-4
        ">

            <span class="
                material-symbols-outlined
                text-[28px]
            ">
                add
            </span>

        </div>


        <h3 class="
            font-headline-md
            text-[18px]
            text-on-surface
            mb-2
        ">
            Create New Project
        </h3>


        <p class="
            font-body-sm
            text-on-surface-variant
            max-w-[200px]
        ">
            Start tracking a new repository or workflow setup.
        </p>

    `;


    card.addEventListener(
        "click",
        function () {

            window.location.href =
                "create-project.html";

        }
    );


    projectGrid.appendChild(card);

}


// =========================================================
// USER PROFILE
// =========================================================

function setupUserProfile() {

    const userProfileBtn =
        document.getElementById(
            "userProfileBtn"
        );

    const profileDropdown =
        document.getElementById(
            "profileDropdown"
        );

    const signOutBtn =
        document.getElementById(
            "signOutBtn"
        );

    const profileArrow =
        document.getElementById(
            "profileArrow"
        );


    // -----------------------------------------------------
    // LOAD USER
    // -----------------------------------------------------

    loadUserProfile();


    // -----------------------------------------------------
    // PROFILE CLICK
    // -----------------------------------------------------

    if (
        userProfileBtn &&
        profileDropdown
    ) {

        userProfileBtn.addEventListener(
            "click",
            function (event) {

                event.stopPropagation();

                profileDropdown.classList.toggle(
                    "hidden"
                );


                if (profileArrow) {

                    profileArrow.classList.toggle(
                        "rotate-180"
                    );

                }

            }
        );

    }


    // -----------------------------------------------------
    // CLICK OUTSIDE
    // -----------------------------------------------------

    document.addEventListener(
        "click",
        function (event) {

            if (
                profileDropdown &&
                userProfileBtn &&
                !userProfileBtn.contains(
                    event.target
                ) &&
                !profileDropdown.contains(
                    event.target
                )
            ) {

                profileDropdown.classList.add(
                    "hidden"
                );


                if (profileArrow) {

                    profileArrow.classList.remove(
                        "rotate-180"
                    );

                }

            }

        }
    );


    // -----------------------------------------------------
    // SIGN OUT
    // -----------------------------------------------------

    if (signOutBtn) {

        signOutBtn.addEventListener(
            "click",
            function () {

                console.log(
                    "Signing out..."
                );


                localStorage.removeItem(
                    "access_token"
                );

                localStorage.removeItem(
                    "user"
                );

                localStorage.removeItem(
                    "user_id"
                );

                localStorage.removeItem(
                    "selected_project_id"
                );


                window.location.href =
                    "../index.html";

            }
        );

    }

}


// =========================================================
// LOAD USER PROFILE
// =========================================================

function loadUserProfile() {

    const userData =
        localStorage.getItem("user");


    if (!userData) {
        return;
    }


    try {

        const user =
            JSON.parse(userData);


        console.log(
            "Logged in user:",
            user
        );


        const name =
            user.name ||
            user.username ||
            "User";


        const email =
            user.email ||
            "User account";


        const role =
            user.role ||
            "Project Member";


        // -------------------------------------------------
        // PROFILE NAME
        // -------------------------------------------------

        const userName =
            document.getElementById(
                "userName"
            );


        if (userName) {

            userName.textContent =
                name;

        }


        // -------------------------------------------------
        // ROLE
        // -------------------------------------------------

        const userRole =
            document.getElementById(
                "userRole"
            );


        if (userRole) {

            userRole.textContent =
                role;

        }


        // -------------------------------------------------
        // DROPDOWN NAME
        // -------------------------------------------------

        const dropdownUserName =
            document.getElementById(
                "dropdownUserName"
            );


        if (dropdownUserName) {

            dropdownUserName.textContent =
                name;

        }


        // -------------------------------------------------
        // DROPDOWN EMAIL
        // -------------------------------------------------

        const dropdownUserEmail =
            document.getElementById(
                "dropdownUserEmail"
            );


        if (dropdownUserEmail) {

            dropdownUserEmail.textContent =
                email;

        }


        // -------------------------------------------------
        // USER INITIAL
        // -------------------------------------------------

        const userProfileInitial =
            document.getElementById(
                "userProfileInitial"
            );


        if (userProfileInitial) {

            userProfileInitial.textContent =
                name
                    .trim()
                    .charAt(0)
                    .toUpperCase() || "U";

        }

    }
    catch (error) {

        console.error(
            "Unable to read user information:",
            error
        );

    }

}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    const div =
        document.createElement("div");


    div.textContent =
        String(value);


    return div.innerHTML;

}