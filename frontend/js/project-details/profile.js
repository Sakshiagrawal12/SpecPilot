// =========================================================
// USER PROFILE
// =========================================================

export function loadUserProfile() {

    const storedUser =
        localStorage.getItem("user");

    if (!storedUser) {
        return;
    }


    let user;

    try {

        user =
            JSON.parse(storedUser);

    } catch (error) {

        console.error(
            "Invalid stored user:",
            error
        );

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
        name.trim().charAt(0).toUpperCase() ||
        "U";


    const userName =
        document.getElementById("userName");


    const profileInitial =
        document.getElementById(
            "userProfileInitial"
        );


    const dropdownUserName =
        document.getElementById(
            "dropdownUserName"
        );


    const dropdownUserEmail =
        document.getElementById(
            "dropdownUserEmail"
        );


    if (userName) {

        userName.textContent =
            name;
    }


    if (profileInitial) {

        profileInitial.textContent =
            initial;
    }


    if (dropdownUserName) {

        dropdownUserName.textContent =
            name;
    }


    if (dropdownUserEmail) {

        dropdownUserEmail.textContent =
            email;
    }
}


// =========================================================
// PROFILE DROPDOWN
// =========================================================

export function setupUserProfile() {

    const profileBtn =
        document.getElementById(
            "userProfileBtn"
        );


    const profileDropdown =
        document.getElementById(
            "profileDropdown"
        );


    const profileArrow =
        document.getElementById(
            "profileArrow"
        );


    const signOutBtn =
        document.getElementById(
            "signOutBtn"
        );


    if (!profileBtn || !profileDropdown) {

        console.warn(
            "Profile dropdown elements not found."
        );

        return;
    }


    // -----------------------------------------------------
    // OPEN / CLOSE DROPDOWN
    // -----------------------------------------------------

    profileBtn.addEventListener(
        "click",
        function (event) {

            event.stopPropagation();

            const isHidden =
                profileDropdown.classList.contains(
                    "hidden"
                );


            if (isHidden) {

                profileDropdown.classList.remove(
                    "hidden"
                );

                if (profileArrow) {

                    profileArrow.classList.add(
                        "rotate-180"
                    );
                }

            } else {

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
    // CLOSE WHEN CLICKING OUTSIDE
    // -----------------------------------------------------

    document.addEventListener(
        "click",
        function (event) {

            if (
                !profileDropdown.contains(
                    event.target
                ) &&
                !profileBtn.contains(
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
            }
        );
    }
}

