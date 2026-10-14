document.addEventListener(
    "DOMContentLoaded",
    () => {

        // =================================================
        // ELEMENTS
        // These IDs must match dashboard.html's markup
        // and the #mainSidebar / #mobileSidebarOverlay /
        // #mobileSidebarClose rules in its <style> block.
        // =================================================

        const sidebar =
            document.getElementById(
                "mainSidebar"
            );

        const overlay =
            document.getElementById(
                "mobileSidebarOverlay"
            );

        const menuButton =
            document.getElementById(
                "mobileMenuButton"
            );

        const closeButton =
            document.getElementById(
                "mobileSidebarClose"
            );


        // =================================================
        // OPEN SIDEBAR
        // =================================================

        function openSidebar() {

            if (!sidebar) return;

            sidebar.classList.add(
                "mobile-sidebar-open"
            );

            if (overlay) {

                overlay.classList.add(
                    "mobile-overlay-visible"
                );
            }

            document.body.classList.add(
                "mobile-sidebar-active"
            );
        }


        // =================================================
        // CLOSE SIDEBAR
        // =================================================

        function closeSidebar() {

            if (!sidebar) return;

            sidebar.classList.remove(
                "mobile-sidebar-open"
            );

            if (overlay) {

                overlay.classList.remove(
                    "mobile-overlay-visible"
                );
            }

            document.body.classList.remove(
                "mobile-sidebar-active"
            );
        }


        // =================================================
        // EVENTS
        // =================================================

        if (menuButton) {

            menuButton.addEventListener(
                "click",
                openSidebar
            );
        }


        if (closeButton) {

            closeButton.addEventListener(
                "click",
                closeSidebar
            );
        }


        if (overlay) {

            overlay.addEventListener(
                "click",
                closeSidebar
            );
        }


        // =================================================
        // CLOSE AFTER NAVIGATION
        // (scoped to links/buttons inside the sidebar itself)
        // =================================================

        if (sidebar) {

            sidebar
                .querySelectorAll(
                    ".sidebar-link"
                )
                .forEach(link => {

                    link.addEventListener(
                        "click",
                        () => {

                            closeSidebar();

                        }
                    );
                });
        }


        // =================================================
        // CLOSE SIDEBAR WHEN SCREEN BECOMES DESKTOP
        // =================================================

        window.addEventListener(
            "resize",
            () => {

                if (
                    window.innerWidth >= 768
                ) {

                    closeSidebar();

                }
            }
        );

// ========================================================
// CURRENT PROJECT
// ========================================================

const projectNameElement =
    document.getElementById(
        "sidebarProjectName"
    );


// --------------------------------------------------------
// GET PROJECT ID FROM CURRENT URL
// --------------------------------------------------------
//
// Agent Chat:
// agent.html?project_id=21&thread_id=abc
//
// Project Details:
// project-details.html?id=21
//

const currentUrlParams =
    new URLSearchParams(
        window.location.search
    );

const urlProjectId =
    currentUrlParams.get("project_id");

const urlDetailsProjectId =
    currentUrlParams.get("id");


// --------------------------------------------------------
// URL PROJECT ID HAS PRIORITY
// --------------------------------------------------------

const currentUrlProjectId =
    urlProjectId ||
    urlDetailsProjectId ||
    null;


// --------------------------------------------------------
// SAVE CURRENT PROJECT ID
// --------------------------------------------------------

if (currentUrlProjectId) {

    localStorage.setItem(
        "selected_project_id",
        String(currentUrlProjectId)
    );

    console.log(
        "SIDEBAR CURRENT PROJECT ID:",
        currentUrlProjectId
    );
}


// --------------------------------------------------------
// READ CURRENT PROJECT
// --------------------------------------------------------

const selectedProjectId =
    localStorage.getItem(
        "selected_project_id"
    );

const selectedProjectName =
    localStorage.getItem(
        "selected_project_name"
    );


// --------------------------------------------------------
// SHOW PROJECT NAME
// --------------------------------------------------------

if (
    projectNameElement &&
    selectedProjectName
) {

    projectNameElement.textContent =
        selectedProjectName;

}

// -------------------------------------------------
// SHOW CURRENT PROJECT NAME
// -------------------------------------------------

if (
    projectNameElement &&
    selectedProjectName
) {

    projectNameElement.textContent =
        selectedProjectName;
}


// -------------------------------------------------
// PROJECT TAB NAVIGATION
// -------------------------------------------------
// PROJECT TAB
const projectTabLink =
    sidebar?.querySelector(
        '.sidebar-link[href*="project-details"], .sidebar-link[data-page="project-details"]'
    );

if (projectTabLink) {

    projectTabLink.addEventListener(
        "click",
        (event) => {

            event.preventDefault();
            event.stopPropagation();

            // First check the current URL
            const currentUrlParams =
                new URLSearchParams(
                    window.location.search
                );

            const urlProjectId =
                currentUrlParams.get("project_id") ||
                currentUrlParams.get("id");

            // Then fallback to localStorage
            const storedProjectId =
                localStorage.getItem(
                    "selected_project_id"
                );

            const currentProjectId =
                urlProjectId ||
                storedProjectId ||
                null;

            console.log(
                "PROJECT TAB CLICKED"
            );

            console.log(
                "URL Project ID:",
                urlProjectId
            );

            console.log(
                "Stored Project ID:",
                storedProjectId
            );

            console.log(
                "Current Project ID:",
                currentProjectId
            );

            if (
                !currentProjectId ||
                currentProjectId === "null" ||
                currentProjectId === "undefined"
            ) {
                alert(
                    "Please select or open a project first."
                );
                return;
            }

            // Keep localStorage synchronized
            localStorage.setItem(
                "selected_project_id",
                String(currentProjectId)
            );

            // Open Project Details for THIS project
            const projectUrl =
                `project-details.html?id=${encodeURIComponent(
                    currentProjectId
                )}`;

            console.log(
                "Navigating to:",
                projectUrl
            );

            window.location.href =
                projectUrl;
        }
    );
}
   

        // =================================================
        // ACTIVE PAGE
        // =================================================

        const currentPage =
            window.location.pathname
                .split("/")
                .pop()
                .replace(".html", "");

        if (sidebar) {

            sidebar
                .querySelectorAll(
                    ".sidebar-link[data-page]"
                )
                .forEach(link => {

                    const page =
                        link.dataset.page;

                    if (
                        page === currentPage ||
                        (
                            page === "project-details" &&
                            currentPage === "project_details"
                        )
                    ) {

                        link.classList.add(
                            "active"
                        );
                    }

                });
        }


        // =================================================
        // LOGOUT
        // =================================================

        const logoutButton =
            document.getElementById(
                "sidebarLogoutButton"
            );

        if (logoutButton) {

            logoutButton.addEventListener(
                "click",
                () => {

                    const confirmed =
                        confirm(
                            "Are you sure you want to logout?"
                        );

                    if (!confirmed) {
                        return;
                    }

                    // Remove authentication
                    localStorage.removeItem(
                        "access_token"
                    );

                    localStorage.removeItem(
                        "user"
                    );

                    // Remove selected project
                    localStorage.removeItem(
                        "selected_project_id"
                    );

                    localStorage.removeItem(
                        "selected_project_name"
                    );

                    // Remove agent session
                    localStorage.removeItem(
                        "agent_thread_id"
                    );

                    // Clear temporary conversation state
                    sessionStorage.clear();

                    window.location.href =
                        "login.html";
                }
            );
        }


        // =================================================
        // PROFILE
        // =================================================

        const profileButton =
            document.getElementById(
                "sidebarProfileButton"
            );

        if (profileButton) {

            profileButton.addEventListener(
                "click",
                () => {

                    window.location.href =
                        "profile.html";
                }
            );
        }

    }
);