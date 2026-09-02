console.log("=================================");
console.log("CREATE PROJECT JS LOADED");
console.log("=================================");


const API_URL = "http://127.0.0.1:8000";


document.addEventListener("DOMContentLoaded", function () {

    console.log("CREATE PROJECT DOM READY");


    // =========================================================
    // ELEMENTS
    // =========================================================

    const projectForm = document.getElementById("projectForm");

    const projectNameInput = document.getElementById("projectName");
    const categoryInput = document.getElementById("category");
    const objectiveInput = document.getElementById("objective");
    const targetUsersInput = document.getElementById("targetUsers");
    const problemStatementInput = document.getElementById("problemStatement");

    const featureInput = document.getElementById("featureInput");
    const addFeatureBtn = document.getElementById("addFeatureBtn");
    const featureList = document.getElementById("featureList");

    const techPrefsInput = document.getElementById("techPrefs");
    const timelineInput = document.getElementById("timeline");
    const instructionsInput = document.getElementById("instructions");

    const cancelButton = document.getElementById("cancelButton");

    const createProjectButton =
        document.getElementById("createProjectButton");

    const createProjectIcon =
        document.getElementById("createProjectIcon");

    const createProjectText =
        document.getElementById("createProjectText");


    // =========================================================
    // CHECK REQUIRED ELEMENTS
    // =========================================================

    if (!projectForm) {
        console.error("projectForm not found.");
        return;
    }

    if (!featureInput) {
        console.error("featureInput not found.");
        return;
    }

    if (!addFeatureBtn) {
        console.error("addFeatureBtn not found.");
        return;
    }

    if (!featureList) {
        console.error("featureList not found.");
        return;
    }


    // =========================================================
    // AUTHENTICATION
    // =========================================================

    const token = localStorage.getItem("access_token");

    console.log("Access token exists:", !!token);

    if (!token) {

        alert("Your session has expired. Please login again.");

        window.location.href = "../index.html";

        return;
    }
setupUserProfile();
// =========================================================
// USER PROFILE
// =========================================================

function setupUserProfile() {

    const userProfileBtn =
        document.getElementById("userProfileBtn");

    const profileDropdown =
        document.getElementById("profileDropdown");

    const signOutBtn =
        document.getElementById("signOutBtn");

    const profileArrow =
        document.getElementById("profileArrow");


    // Load logged-in user
    loadUserProfile();


    // -----------------------------------------------------
    // PROFILE BUTTON
    // -----------------------------------------------------

    if (userProfileBtn && profileDropdown) {

        userProfileBtn.addEventListener(
            "click",
            function (event) {

                event.stopPropagation();

                profileDropdown.classList.toggle("hidden");

                if (profileArrow) {

                    profileArrow.classList.toggle(
                        "rotate-180"
                    );

                }

            }
        );

    }


    // -----------------------------------------------------
    // CLICK OUTSIDE DROPDOWN
    // -----------------------------------------------------

    document.addEventListener(
        "click",
        function (event) {

            if (
                profileDropdown &&
                userProfileBtn &&
                !userProfileBtn.contains(event.target) &&
                !profileDropdown.contains(event.target)
            ) {

                profileDropdown.classList.add("hidden");

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


    console.log(
        "Stored user data:",
        userData
    );


    if (!userData) {

        console.warn(
            "No user data found in localStorage."
        );

        return;

    }


    try {

        const user =
            JSON.parse(userData);


        console.log(
            "Logged in user:",
            user
        );


        // -------------------------------------------------
        // SAME LOGIC AS DASHBOARD.JS
        // -------------------------------------------------

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
        // USER NAME
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
        // USER ROLE
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
    // FEATURES
    // =========================================================

    let features = [];


    // =========================================================
    // ADD FEATURE
    // =========================================================

    addFeatureBtn.addEventListener("click", addFeature);


    featureInput.addEventListener("keydown", function (event) {

        if (event.key === "Enter") {

            event.preventDefault();

            addFeature();

        }

    });


    function addFeature() {

        const feature = featureInput.value.trim();


        if (!feature) {

            return;

        }


        // Prevent duplicate features

        if (
            features.some(
                existingFeature =>
                    existingFeature.toLowerCase() === feature.toLowerCase()
            )
        ) {

            alert("This feature has already been added.");

            return;

        }


        features.push(feature);

        featureInput.value = "";

        renderFeatures();

        featureInput.focus();

    }


    // =========================================================
    // REMOVE FEATURE
    // =========================================================

    function removeFeature(index) {

        features.splice(index, 1);

        renderFeatures();

    }


    // =========================================================
    // RENDER FEATURES
    // =========================================================

    function renderFeatures() {

        featureList.innerHTML = "";


        features.forEach(function (feature, index) {

            const li = document.createElement("li");

            li.className =
                "flex items-center justify-between " +
                "bg-surface-container-low " +
                "px-4 py-3 " +
                "rounded-lg " +
                "border border-outline-variant/50";


            li.innerHTML = `

                <div class="flex items-center gap-3 min-w-0">

                    <span
                        class="material-symbols-outlined text-primary text-[18px]"
                    >
                        check_circle
                    </span>

                    <span
                        class="font-body-sm text-body-sm text-on-surface truncate"
                    >
                        ${escapeHtml(feature)}
                    </span>

                </div>


                <button
                    type="button"
                    class="text-outline hover:text-error transition-colors ml-3 shrink-0"
                    aria-label="Remove feature"
                >

                    <span class="material-symbols-outlined text-[18px]">
                        close
                    </span>

                </button>

            `;


            const removeButton =
                li.querySelector("button");


            removeButton.addEventListener(
                "click",
                function () {

                    removeFeature(index);

                }
            );


            featureList.appendChild(li);

        });

    }


    // =========================================================
    // FORM SUBMIT
    // =========================================================

    projectForm.addEventListener("submit", async function (event) {

        event.preventDefault();


        console.log("================================");
        console.log("PROJECT FORM SUBMITTED");
        console.log("================================");


        // -----------------------------------------------------
        // GET VALUES
        // -----------------------------------------------------

        const projectName =
            projectNameInput.value.trim();

        const category =
            categoryInput.value;

        const objective =
            objectiveInput.value.trim();

        const targetUsers =
            targetUsersInput.value.trim();

        const problemStatement =
            problemStatementInput.value.trim();

        const techPrefs =
            techPrefsInput.value.trim();

        const timeline =
            timelineInput.value;

        const instructions =
            instructionsInput.value.trim();


        // -----------------------------------------------------
        // VALIDATION
        // -----------------------------------------------------

        if (!projectName) {

            alert("Please enter the project name.");

            projectNameInput.focus();

            return;

        }


        if (!category) {

            alert("Please select a category.");

            categoryInput.focus();

            return;

        }


        if (!objective) {

            alert("Please enter the business objective.");

            objectiveInput.focus();

            return;

        }


        if (!targetUsers) {

            alert("Please enter the target users.");

            targetUsersInput.focus();

            return;

        }


        if (!problemStatement) {

            alert("Please enter the problem statement.");

            problemStatementInput.focus();

            return;

        }


        if (features.length === 0) {

            alert("Please add at least one expected feature.");

            featureInput.focus();

            return;

        }


        if (!techPrefs) {

            alert("Please enter technology preferences.");

            techPrefsInput.focus();

            return;

        }


        if (!timeline) {

            alert("Please select a timeline.");

            timelineInput.focus();

            return;

        }


        // -----------------------------------------------------
        // REQUEST DATA
        // -----------------------------------------------------

        const projectData = {

            project_name: projectName,

            category: category,

            business_objective: objective,

            target_users: targetUsers,

            problem_statement: problemStatement,

            expected_features: features.join(", "),

            technology_preferences: techPrefs,

            timeline: timeline,

            additional_instructions:
                instructions || null

        };


        console.log(
            "Project data being sent:",
            projectData
        );


        // -----------------------------------------------------
        // DISABLE BUTTON
        // -----------------------------------------------------

        createProjectButton.disabled = true;

        createProjectButton.classList.add(
            "opacity-70",
            "cursor-not-allowed"
        );


        createProjectIcon.textContent = "progress_activity";

        createProjectIcon.classList.add(
            "animate-spin"
        );


        createProjectText.textContent =
            "Creating Project...";


        // -----------------------------------------------------
        // API REQUEST
        // -----------------------------------------------------

        try {

            const response = await fetch(
                `${API_URL}/projects/`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },

                    body: JSON.stringify(projectData)
                }
            );


            // -------------------------------------------------
            // RESPONSE
            // -------------------------------------------------

            let data = {};

            try {

                data = await response.json();

            } catch (jsonError) {

                console.warn(
                    "Response was not valid JSON."
                );

            }


            console.log(
                "Backend status:",
                response.status
            );

            console.log(
                "Backend response:",
                data
            );


            // -------------------------------------------------
            // UNAUTHORIZED
            // -------------------------------------------------

            if (response.status === 401) {

                alert(
                    "Your session has expired. Please login again."
                );

                localStorage.removeItem("access_token");
                localStorage.removeItem("user_id");
                localStorage.removeItem("user");

                window.location.href =
                    "../index.html";

                return;

            }


            // -------------------------------------------------
            // OTHER ERRORS
            // -------------------------------------------------

            if (!response.ok) {

                let errorMessage =
                    "Failed to create project.";


                if (data.detail) {

                    if (Array.isArray(data.detail)) {

                        errorMessage =
                            data.detail
                                .map(error => {

                                    return error.msg ||
                                        "Invalid value.";

                                })
                                .join("\n");

                    } else {

                        errorMessage =
                            data.detail;

                    }

                }


                alert(errorMessage);

                resetCreateButton();

                return;

            }


            // -------------------------------------------------
            // SUCCESS
            // -------------------------------------------------

            console.log(
                "Project created successfully."
            );

            console.log(
                "Created project ID:",
                data.project_id
            );


            alert(
                "Project created successfully!"
            );


            // -------------------------------------------------
            // IMPORTANT
            // -------------------------------------------------
            // Do NOT go to projectForm.
            // Do NOT go directly to project-details.
            //
            // First return to dashboard.
            // Dashboard will show the new project.
            // -------------------------------------------------

            window.location.href =
                "dashboard.html";

        } catch (error) {

            console.error(
                "PROJECT CREATION ERROR:",
                error
            );


            alert(
                "Unable to connect to the backend. " +
                "Make sure FastAPI is running at " +
                API_URL
            );


            resetCreateButton();

        }

    });


    // =========================================================
    // CANCEL
    // =========================================================

    cancelButton.addEventListener(
        "click",
        function () {

            window.location.href =
                "dashboard.html";

        }
    );


    // =========================================================
    // RESET CREATE BUTTON
    // =========================================================

    function resetCreateButton() {

        createProjectButton.disabled = false;

        createProjectButton.classList.remove(
            "opacity-70",
            "cursor-not-allowed"
        );


        createProjectIcon.textContent = "add";

        createProjectIcon.classList.remove(
            "animate-spin"
        );


        createProjectText.textContent =
            "Create Project";

    }


    // =========================================================
    // ESCAPE HTML
    // =========================================================

    function escapeHtml(text) {

        const div =
            document.createElement("div");

        div.textContent = text;

        return div.innerHTML;

    }


    console.log(
        "Create project page initialized successfully."
    );

});