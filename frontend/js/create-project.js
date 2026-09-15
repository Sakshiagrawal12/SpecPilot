console.log("=================================");
console.log("SPEC PILOT CREATE PROJECT LOADED");
console.log("=================================");


// =========================================================
// CONFIGURATION
// =========================================================

const API_URL = "http://127.0.0.1:8000";


// =========================================================
// DOM
// =========================================================

document.addEventListener("DOMContentLoaded", () => {

    const projectForm =
        document.getElementById("projectForm");

    const projectNameInput =
        document.getElementById("projectName");

    const cancelButton =
        document.getElementById("cancelButton");

    const createProjectButton =
        document.getElementById("createProjectButton");

    const createProjectButtonText =
        document.getElementById("createProjectButtonText");

    const createProjectButtonIcon =
        document.getElementById("createProjectButtonIcon");


    // =========================================================
    // AUTH
    // =========================================================

    const token =
        localStorage.getItem("access_token");


    if (!token) {

        alert(
            "Your session has expired. Please login again."
        );

        window.location.href =
            "../index.html";

        return;
    }


    // =========================================================
    // USER PROFILE
    // =========================================================

    loadUserProfile();


    // =========================================================
    // FORM SUBMIT
    // =========================================================

    if (projectForm) {

        projectForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();

                await createProject();

            }
        );

    }


    // =========================================================
    // CANCEL
    // =========================================================

    if (cancelButton) {

        cancelButton.addEventListener(
            "click",
            () => {

                window.location.href =
                    "dashboard.html";

            }
        );

    }


    // =========================================================
    // CREATE PROJECT
    // =========================================================

    async function createProject() {

        const projectName =
            projectNameInput?.value?.trim();


        // -----------------------------------------------------
        // VALIDATION
        // -----------------------------------------------------

        if (!projectName) {

            alert(
                "Please enter a project name."
            );

            projectNameInput?.focus();

            return;
        }


        // -----------------------------------------------------
        // LOADING STATE
        // -----------------------------------------------------

        setLoadingState(true);


        try {

            console.log(
                "Creating project:",
                projectName
            );


            // -------------------------------------------------
            // API REQUEST
            // -------------------------------------------------

            const response =
                await fetch(
                    `${API_URL}/projects/`,
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "Authorization":
                                `Bearer ${token}`

                        },

                        body: JSON.stringify({

                            project_name:
                                projectName

                        })

                    }
                );


            // -------------------------------------------------
            // AUTH ERROR
            // -------------------------------------------------

            if (response.status === 401) {

                localStorage.removeItem(
                    "access_token"
                );

                localStorage.removeItem(
                    "user"
                );

                alert(
                    "Your session has expired. Please login again."
                );

                window.location.href =
                    "../index.html";

                return;
            }


            // -------------------------------------------------
            // READ RESPONSE
            // -------------------------------------------------

            const data =
                await response.json();


            console.log(
                "CREATE PROJECT RESPONSE:",
                data
            );


            // -------------------------------------------------
            // API ERROR
            // -------------------------------------------------

            if (!response.ok) {

                console.error(
                    "CREATE PROJECT ERROR:",
                    data
                );

                let errorMessage =
                    "Unable to create project.";


                if (data.detail) {

                    if (
                        Array.isArray(data.detail)
                    ) {

                        errorMessage =
                            data.detail
                                .map(
                                    error => error.msg
                                )
                                .join("\n");

                    }

                    else {

                        errorMessage =
                            data.detail;

                    }

                }


                throw new Error(
                    errorMessage
                );

            }


            // -------------------------------------------------
            // GET PROJECT ID
            // -------------------------------------------------

            const projectId =
                data.project_id;


            if (!projectId) {

                throw new Error(
                    "Project was created but no project ID was returned."
                );

            }


            // -------------------------------------------------
            // GET PROJECT NAME
            // -------------------------------------------------

            const createdProjectName =
                data.project_name ||
                projectName;


            console.log(
                "PROJECT CREATED:",
                {
                    projectId,
                    projectName: createdProjectName
                }
            );


            // =================================================
            // SAVE PROJECT INFORMATION
            // =================================================

            localStorage.setItem(
                "selected_project_id",
                String(projectId)
            );


            localStorage.setItem(
                "selected_project_name",
                createdProjectName
            );


            // =================================================
            // CREATE AGENT THREAD
            // =================================================

            const threadId =
                crypto.randomUUID();


            localStorage.setItem(
                "agent_thread_id",
                threadId
            );


            console.log(
                "AGENT THREAD CREATED:",
                threadId
            );


            // =================================================
            // REDIRECT TO AGENT
            // =================================================

            window.location.href =
                `agent.html?project_id=${encodeURIComponent(projectId)}&thread_id=${encodeURIComponent(threadId)}`;

        }


        catch (error) {

            console.error(
                "PROJECT CREATION FAILED:",
                error
            );


            alert(
                error.message ||
                "Something went wrong while creating the project."
            );

        }


        finally {

            setLoadingState(false);

        }

    }


    // =========================================================
    // LOADING STATE
    // =========================================================

    function setLoadingState(isLoading) {

        if (!createProjectButton) {
            return;
        }


        createProjectButton.disabled =
            isLoading;


        if (createProjectButtonText) {

            createProjectButtonText.textContent =
                isLoading
                    ? "Creating..."
                    : "Start with Agent";

        }


        if (createProjectButtonIcon) {

            createProjectButtonIcon.textContent =
                isLoading
                    ? "hourglass_empty"
                    : "smart_toy";

        }

    }


    // =========================================================
    // USER PROFILE
    // =========================================================

    function loadUserProfile() {

        try {

            const userString =
                localStorage.getItem("user");


            console.log(
                "USER FROM LOCAL STORAGE:",
                userString
            );


            if (!userString) {

                console.warn(
                    "No user information found in localStorage."
                );

                return;

            }


            const user =
                JSON.parse(userString);


            const name =
                user.name ||
                user.username ||
                user.full_name ||
                user.fullName ||
                user.email ||
                "User";


            const email =
                user.email ||
                "";


            const initial =
                name
                    .charAt(0)
                    .toUpperCase();


            const nameElement =
                document.getElementById(
                    "userProfileName"
                );


            if (nameElement) {

                nameElement.textContent =
                    name;

            }


            const initialElement =
                document.getElementById(
                    "userProfileInitial"
                );


            if (initialElement) {

                initialElement.textContent =
                    initial;

            }


            const emailElement =
                document.getElementById(
                    "userEmail"
                );


            if (emailElement) {

                emailElement.textContent =
                    email;

            }


        }

        catch (error) {

            console.error(
                "USER PROFILE ERROR:",
                error
            );

        }

    }

});