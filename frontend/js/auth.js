// =========================================================
// SPEC PILOT AUTHENTICATION
// =========================================================


// =========================================================
// GET ACCESS TOKEN
// =========================================================

function getAccessToken() {

    return localStorage.getItem(
        "access_token"
    );

}


// =========================================================
// GET CURRENT USER
// =========================================================

function getCurrentUser() {

    const user =
        localStorage.getItem(
            "user"
        );


    if (!user) {

        return null;

    }


    try {

        return JSON.parse(user);

    }

    catch (error) {

        console.error(
            "Unable to read user information:",
            error
        );

        return null;

    }

}


// =========================================================
// CHECK AUTHENTICATION
// =========================================================

function requireAuthentication() {

    const token =
        getAccessToken();


    const user =
        getCurrentUser();


    if (!token || !user) {

        window.location.href =
            "../index.html";

        return false;

    }


    return true;

}


// =========================================================
// DISPLAY USER NAME
// =========================================================

function displayCurrentUser() {

    const user =
        getCurrentUser();


    if (!user) {

        return;

    }


    const userNameElements =
        document.querySelectorAll(
            "[data-user-name]"
        );


    userNameElements.forEach(
        function (element) {

            element.textContent =
                user.name;

        }
    );


    const userInitialElements =
        document.querySelectorAll(
            "[data-user-initial]"
        );


    userInitialElements.forEach(
        function (element) {

            element.textContent =
                user.name
                    ? user.name
                        .charAt(0)
                        .toUpperCase()
                    : "U";

        }
    );

}


// =========================================================
// SIGN OUT
// =========================================================

function signOut() {

    console.log(
        "Signing out..."
    );


    // Remove authentication information

    localStorage.removeItem(
        "access_token"
    );


    localStorage.removeItem(
        "user_id"
    );


    localStorage.removeItem(
        "user"
    );


    // Redirect to login

    window.location.href =
        "../index.html";

}


// =========================================================
// SETUP SIGN OUT BUTTONS
// =========================================================

function setupSignOut() {

    const signOutButtons =
        document.querySelectorAll(
            "[data-signout]"
        );


    signOutButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    const confirmed =
                        confirm(
                            "Are you sure you want to sign out?"
                        );


                    if (confirmed) {

                        signOut();

                    }

                }
            );

        }
    );

}


// =========================================================
// INITIALIZE AUTH UI
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        if (
            getAccessToken() &&
            getCurrentUser()
        ) {

            displayCurrentUser();

            setupSignOut();

        }

    }
);
