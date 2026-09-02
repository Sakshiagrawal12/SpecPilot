const loginForm =
    document.getElementById("loginForm");


console.log("LOGIN JS LOADED");


if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const email =
                document
                    .getElementById("email")
                    .value
                    .trim();


            const password =
                document
                    .getElementById("password")
                    .value;


            try {

                const response =
                    await fetch(
                        "http://127.0.0.1:8000/auth/login",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                email:
                                    email,

                                password:
                                    password

                            })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    alert(
                        data.detail ||
                        "Invalid email or password"
                    );

                    return;
                }


                // =========================================
                // SAVE LOGIN SESSION
                // =========================================

                localStorage.setItem(
                    "access_token",
                    data.access_token
                );


                localStorage.setItem(
                    "user",
                    JSON.stringify(data.user)
                );


                localStorage.setItem(
                    "user_id",
                    data.user.id
                );


                console.log(
                    "Logged in user:",
                    data.user
                );


                // =========================================
                // REDIRECT
                // =========================================

                window.location.href =
                    "./pages/dashboard.html";

            }


            catch (error) {

                console.error(
                    "Login error:",
                    error
                );


                alert(
                    "Unable to connect to SpecPilot backend."
                );

            }

        }
    );

}