// ============================================================
// SPEC PILOT AGENT
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("=================================");
    console.log("SPEC PILOT AGENT LOADED");
    console.log("TIME:", new Date().toISOString());
    console.log("URL:", window.location.href);
    console.log("=================================");


    // ========================================================
    // ELEMENTS
    // ========================================================

    const projectSelect =
        document.getElementById("projectSelect");

    const conversationArea =
        document.getElementById("conversationArea");

    const emptyState =
        document.getElementById("emptyState");

    const messageInput =
        document.getElementById("messageInput");

    const sendButton =
        document.getElementById("sendButton");

    const sendIcon =
        document.getElementById("sendIcon");

    const newProjectButton =
        document.getElementById("newProjectButton");

    const generatePrdButton =
    document.getElementById("generatePrdButton");

    const userProfileName =
        document.getElementById("userProfileName");

    const userProfileInitial =
        document.getElementById("userProfileInitial");


    // ========================================================
    // CONFIGURATION
    // ========================================================

    const API_BASE_URL =
        "http://127.0.0.1:8000";


    // ========================================================
    // STATE
    // ========================================================

    let selectedProjectId = null;

    let selectedProjectName = null;

    let threadId = null;

    let isSending = false;


    // ========================================================
    // AUTHENTICATION
    // ========================================================

    const token =
        localStorage.getItem("access_token");


    if (!token) {

        console.warn(
            "No access token found."
        );

        window.location.href =
            "../index.html";

        return;

    }


    // ========================================================
    // URL PARAMETERS
    // ========================================================

    const urlParams =
        new URLSearchParams(
            window.location.search
        );


    const urlProjectId =
        urlParams.get("project_id");


    const urlThreadId =
        urlParams.get("thread_id");


    console.log(
        "URL PROJECT ID:",
        urlProjectId
    );


    console.log(
        "URL THREAD ID:",
        urlThreadId
    );


    // ========================================================
    // LOCAL STORAGE
    // ========================================================

    const storedProjectId =
        localStorage.getItem(
            "selected_project_id"
        );


    const storedProjectName =
        localStorage.getItem(
            "selected_project_name"
        );


    const storedThreadId =
        localStorage.getItem(
            "agent_thread_id"
        );


    console.log(
        "STORED PROJECT ID:",
        storedProjectId
    );


    console.log(
        "STORED PROJECT NAME:",
        storedProjectName
    );


    console.log(
        "STORED THREAD ID:",
        storedThreadId
    );


    // ========================================================
    // DETERMINE PROJECT
    // ========================================================

    selectedProjectId =
        urlProjectId ||
        storedProjectId ||
        null;


    selectedProjectName =
        storedProjectName ||
        null;


    // ========================================================
    // DETERMINE THREAD
    // ========================================================

    threadId =
        urlThreadId ||
        storedThreadId ||
        null;


    if (!threadId) {

        threadId =
            crypto.randomUUID();


        localStorage.setItem(
            "agent_thread_id",
            threadId
        );

    }


    console.log(
        "SELECTED PROJECT:",
        selectedProjectId
    );


    console.log(
        "SELECTED PROJECT NAME:",
        selectedProjectName
    );


    console.log(
        "AGENT THREAD:",
        threadId
    );

function lockAgentChat() {

    if (messageInput) {
        messageInput.disabled = true;
        messageInput.value = "";
        messageInput.placeholder =
            "Requirements completed. Generate your PRD.";
    }

    if (sendButton) {
        sendButton.disabled = true;
    }
    console.log("Agent Chat Locked");

}
//----------------------------------------
// Show and hide PRD button
//----------------------------------------

function updatePrdButton(data) {

    if (!generatePrdButton) {
        return;
    }

    const isComplete =
        data?.completeness_status === "COMPLETE" &&
        data?.next_action === "generate_prd" &&
        data?.current_field === null;

    if (isComplete) {

        generatePrdButton.classList.remove("hidden");

        console.log("=================================");
        console.log("PRD GENERATION IS READY");
        console.log("=================================");

    } else {

        generatePrdButton.classList.add("hidden");

    }
}
// ============================================================
// GENERATE PRD BUTTON
// ============================================================

if (generatePrdButton) {

    generatePrdButton.addEventListener(
        "click",
        () => {

            if (!selectedProjectId) {

                alert(
                    "Please select a project first."
                );

                return;

            }


            console.log(
                "GENERATING PRD FOR PROJECT:",
                selectedProjectId
            );


            window.location.href =
                `project-details.html?project_id=${selectedProjectId}`;

        }
    );

}
    // ========================================================
    // NEW PROJECT BUTTON
    // ========================================================

    if (newProjectButton) {

        newProjectButton.addEventListener(
            "click",
            () => {

                window.location.href =
                    "create-project.html";

            }
        );

    }


    // ========================================================
    // INITIALIZE
    // ========================================================

    initializeAgent();


    // ========================================================
    // INITIALIZE AGENT
    // ========================================================

    // ========================================================
// INITIALIZE AGENT
// ========================================================

// ========================================================
// INITIALIZE AGENT
// ========================================================

async function initializeAgent() {

    console.trace("🔥🔥 initializeAgent() CALLED");

    console.log(
        "🔥 initializeAgent TIME:",
        new Date().toISOString()
    );

    try {

        // ------------------------------------------------
        // USER
        // ------------------------------------------------

        loadUserProfile();


        // ------------------------------------------------
        // LOAD PROJECTS
        // ------------------------------------------------

        await loadProjects();


        // ------------------------------------------------
        // SELECT CURRENT PROJECT
        // ------------------------------------------------

        if (!selectedProjectId) {

            console.log(
                "No project selected."
            );

            return;
        }


        const currentOption =
            [...projectSelect.options].find(
                option =>
                    option.value ===
                    String(selectedProjectId)
            );


        if (!currentOption) {

            console.warn(
                "Current project not found in dropdown."
            );

            return;
        }


        // ------------------------------------------------
        // SET PROJECT
        // ------------------------------------------------

        projectSelect.value =
            String(selectedProjectId);


        selectedProjectName =
            currentOption.dataset.projectName ||
            currentOption.textContent.trim();


        localStorage.setItem(
            "selected_project_id",
            String(selectedProjectId)
        );


        localStorage.setItem(
            "selected_project_name",
            selectedProjectName
        );


        console.log(
            "CURRENT PROJECT:",
            selectedProjectId
        );


        console.log(
            "CURRENT PROJECT NAME:",
            selectedProjectName
        );


        // ------------------------------------------------
        // TRY DATABASE HISTORY FIRST
        // ------------------------------------------------

        const historyLoaded =
            await loadAgentHistory();


        // ------------------------------------------------
        // EXISTING CONVERSATION
        // ------------------------------------------------

        if (historyLoaded) {

            console.log(
                "================================="
            );

            console.log(
                "EXISTING CONVERSATION RESTORED"
            );

            console.log(
                "Skipping /agent/start"
            );

            console.log(
                "================================="
            );

            return;
        }


        // ------------------------------------------------
        // NEW CONVERSATION
        // ------------------------------------------------

        console.log(
            "No existing conversation found."
        );


        await startInitialConversation();

    }

    catch (error) {

        console.error(
            "AGENT INITIALIZATION ERROR:",
            error
        );

    }

}

// ========================================================
// GET CHAT STORAGE KEY
// ========================================================

function getConversationStorageKey() {

    if (!selectedProjectId || !threadId) {

        return null;
    }


    return `conversation_${selectedProjectId}_${threadId}`;

}


// ========================================================
// SAVE MESSAGE
// ========================================================

function saveMessage(role, message) {

    const key =
        getConversationStorageKey();


    if (!key) {
        return;
    }


    let messages = [];


    try {

        messages =
            JSON.parse(
                sessionStorage.getItem(key)
            ) || [];

    }

    catch (error) {

        messages = [];

    }


    messages.push({
        role: role,
        message: message
    });


    sessionStorage.setItem(
        key,
        JSON.stringify(messages)
    );

}

    // ========================================================
    // LOAD USER PROFILE
    // ========================================================

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
                    "No user object found in localStorage."
                );

                return;

            }


            const user =
                JSON.parse(userString);


            console.log(
                "PARSED USER:",
                user
            );


            const userName =
                user.name ||
                user.username ||
                user.full_name ||
                user.fullName ||
                user.email ||
                "User";


            // ------------------------------------------------
            // PROFILE NAME
            // ------------------------------------------------

            if (userProfileName) {

                userProfileName.textContent =
                    userName;

            }


            // ------------------------------------------------
            // PROFILE INITIAL
            // ------------------------------------------------

            if (userProfileInitial) {

                userProfileInitial.textContent =
                    userName
                        .charAt(0)
                        .toUpperCase();

            }


            console.log(
                "DISPLAYED USER NAME:",
                userName
            );

        }

        catch (error) {

            console.error(
                "USER PROFILE ERROR:",
                error
            );

        }

    }
// ========================================================
// LOAD PROJECTS
// ========================================================

async function loadProjects() {

    console.log("=================================");
    console.log("Loading projects...");
    console.log("=================================");

    if (!projectSelect) {

        console.error(
            "PROJECT SELECT ELEMENT NOT FOUND."
        );

        return;

    }


    try {

        // ------------------------------------------------
        // GET PROJECTS
        // ------------------------------------------------

        const response =
            await fetch(
                `${API_BASE_URL}/projects/`,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"
                    }
                }
            );


        // ------------------------------------------------
        // AUTH ERROR
        // ------------------------------------------------

        if (response.status === 401) {

            console.warn(
                "Session expired."
            );

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "user"
            );

            localStorage.removeItem(
                "selected_project_id"
            );

            localStorage.removeItem(
                "selected_project_name"
            );

            localStorage.removeItem(
                "agent_thread_id"
            );

            window.location.href =
                "../index.html";

            return;

        }


        // ------------------------------------------------
        // RESPONSE ERROR
        // ------------------------------------------------

        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "LOAD PROJECTS ERROR:",
                response.status,
                errorText
            );

            throw new Error(
                `Failed to load projects (${response.status})`
            );

        }


        // ------------------------------------------------
        // PARSE RESPONSE
        // ------------------------------------------------

        const projects =
            await response.json();


        console.log(
            "PROJECTS:",
            projects
        );


        if (!Array.isArray(projects)) {

            console.error(
                "Unexpected projects response:",
                projects
            );

            throw new Error(
                "Projects API did not return an array."
            );

        }


        // ------------------------------------------------
        // CLEAR DROPDOWN
        // ------------------------------------------------

        projectSelect.innerHTML = "";


        // ------------------------------------------------
        // DEFAULT OPTION
        // ------------------------------------------------

        const defaultOption =
            document.createElement("option");

        defaultOption.value = "";

        defaultOption.textContent =
            "Select Project...";

        projectSelect.appendChild(
            defaultOption
        );


        // ------------------------------------------------
        // ADD PROJECTS TO DROPDOWN
        // ------------------------------------------------

        projects.forEach(project => {

            const projectId =
                project.id ??
                project.project_id;


            const projectName =
                project.project_name ??
                project.name ??
                "Unnamed Project";


            if (projectId == null) {

                console.warn(
                    "Project has no ID:",
                    project
                );

                return;

            }


            const option =
                document.createElement("option");


            option.value =
                String(projectId);


            option.textContent =
                String(projectName);


            // Store name directly on option
            option.dataset.projectName =
                String(projectName);


            projectSelect.appendChild(
                option
            );


            console.log(
                "ADDING PROJECT:",
                {
                    id: projectId,
                    name: projectName
                }
            );

        });


        // ------------------------------------------------
        // DETERMINE CURRENT PROJECT
        // ------------------------------------------------

        const currentProjectId =
            urlProjectId ||
            localStorage.getItem(
                "selected_project_id"
            );


        console.log(
            "CURRENT PROJECT ID:",
            currentProjectId
        );


        // ------------------------------------------------
        // SELECT CURRENT PROJECT
        // ------------------------------------------------

        if (currentProjectId) {

            const currentOption =
                [...projectSelect.options]
                    .find(
                        option =>
                            option.value ===
                            String(currentProjectId)
                    );


            if (currentOption) {

                // ----------------------------------------
                // SELECT OPTION
                // ----------------------------------------

                projectSelect.value =
                    String(currentProjectId);


                // ----------------------------------------
                // UPDATE STATE
                // ----------------------------------------

                selectedProjectId =
                    String(currentProjectId);


                selectedProjectName =
                    currentOption.dataset.projectName ||
                    currentOption.textContent.trim();


                // ----------------------------------------
                // SAVE STATE
                // ----------------------------------------

                localStorage.setItem(
                    "selected_project_id",
                    selectedProjectId
                );


                localStorage.setItem(
                    "selected_project_name",
                    selectedProjectName
                );


                console.log(
                    "CURRENT PROJECT:",
                    selectedProjectId
                );


                console.log(
                    "CURRENT PROJECT NAME:",
                    selectedProjectName
                );

            }

            else {

                console.warn(
                    "Selected project was not found:",
                    currentProjectId
                );

                selectedProjectId = null;

                selectedProjectName = null;

                projectSelect.value = "";

            }

        }

        else {

            selectedProjectId = null;

            selectedProjectName = null;

            projectSelect.value = "";

        }


        // ------------------------------------------------
        // FINAL LOG
        // ------------------------------------------------

        console.log(
            "PROJECT DROPDOWN UPDATED."
        );

        console.log(
            "TOTAL PROJECTS:",
            projects.length
        );

        console.log(
            "SELECTED ID:",
            selectedProjectId
        );

        console.log(
            "SELECTED NAME:",
            selectedProjectName
        );

    }

    catch (error) {

        console.error(
            "LOAD PROJECTS ERROR:",
            error
        );


        projectSelect.innerHTML = "";


        const errorOption =
            document.createElement("option");

        errorOption.value = "";

        errorOption.textContent =
            "Unable to load projects";


        projectSelect.appendChild(
            errorOption
        );

    }

}

// ============================================================
// PROJECT SELECT CHANGE
// ============================================================

if (projectSelect) {

    projectSelect.addEventListener(
        "change",
        async () => {

            console.log("=================================");
            console.log("PROJECT DROPDOWN CHANGE FIRED");
            console.log("=================================");


            // ------------------------------------------------
            // GET SELECTED PROJECT
            // ------------------------------------------------

            const projectId =
                projectSelect.value;


            console.log(
                "NEW PROJECT ID:",
                projectId
            );


            // ------------------------------------------------
            // NO PROJECT SELECTED
            // ------------------------------------------------

            if (!projectId) {

                selectedProjectId = null;
                selectedProjectName = null;
                threadId = null;

                localStorage.removeItem(
                    "selected_project_id"
                );

                localStorage.removeItem(
                    "selected_project_name"
                );

                localStorage.removeItem(
                    "agent_thread_id"
                );


                // Clear UI WITHOUT confirmation.
                resetConversationUI();

                return;
            }


            // ------------------------------------------------
            // GET SELECTED OPTION
            // ------------------------------------------------

            const selectedOption =
                projectSelect.options[
                    projectSelect.selectedIndex
                ];


            // ------------------------------------------------
            // UPDATE PROJECT STATE
            // ------------------------------------------------

            selectedProjectId =
                String(projectId);

            selectedProjectName =
                selectedOption?.dataset?.projectName ||
                selectedOption?.textContent?.trim() ||
                "your project";


            console.log(
                "NEW PROJECT NAME:",
                selectedProjectName
            );


            // ------------------------------------------------
            // SAVE PROJECT
            // ------------------------------------------------

            localStorage.setItem(
                "selected_project_id",
                selectedProjectId
            );

            localStorage.setItem(
                "selected_project_name",
                selectedProjectName
            );


            // ------------------------------------------------
            // CREATE A NEW FRONTEND THREAD
            // ------------------------------------------------
            //
            // This thread is only for the new project context.
            // Backend history will replace it if an existing
            // conversation already exists.
            //

            threadId =
                crypto.randomUUID();


            localStorage.setItem(
                "agent_thread_id",
                threadId
            );


            console.log(
                "NEW THREAD ID:",
                threadId
            );


            // ------------------------------------------------
            // UPDATE URL
            // ------------------------------------------------

            const newUrl =
                new URL(
                    window.location.href
                );


            newUrl.searchParams.set(
                "project_id",
                selectedProjectId
            );

            newUrl.searchParams.set(
                "thread_id",
                threadId
            );


            window.history.replaceState(
                {},
                "",
                newUrl
            );


            // ------------------------------------------------
            // IMPORTANT:
            // DO NOT CALL clearConversation()
            //
            // clearConversation() asks for confirmation.
            // Project switching should be silent.
            // ------------------------------------------------

            resetConversationUI();


            // ------------------------------------------------
            // LOAD THE SELECTED PROJECT'S HISTORY
            // ------------------------------------------------

            const historyLoaded =
                await loadAgentHistory();


            // ------------------------------------------------
            // EXISTING PROJECT CONVERSATION
            // ------------------------------------------------

            if (historyLoaded) {

                console.log(
                    "Existing conversation restored for:",
                    selectedProjectName
                );

                return;
            }


            // ------------------------------------------------
            // NEW PROJECT CONVERSATION
            // ------------------------------------------------

            console.log(
                "No conversation found for:",
                selectedProjectName
            );


            await startInitialConversation();

        }
    );

}



// ============================================================
// LOAD AGENT HISTORY FROM BACKEND
// ============================================================

async function loadAgentHistory() {

    if (!selectedProjectId) {

        console.warn(
            "Cannot load history without project ID."
        );

        return false;
    }


    try {

        console.log(
            "================================="
        );

        console.log(
            "LOADING AGENT HISTORY"
        );

        console.log(
            "PROJECT ID:",
            selectedProjectId
        );

        console.log(
            "================================="
        );


        const response =
            await fetch(
                `${API_BASE_URL}/agent/history/${selectedProjectId}`,
                {

                    method: "GET",

                    headers: {

                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"

                    }

                }
            );


        // ------------------------------------------------
        // API ERROR
        // ------------------------------------------------

        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "HISTORY API ERROR:",
                response.status,
                errorText
            );

            return false;
        }


        // ------------------------------------------------
        // RESPONSE
        // ------------------------------------------------

        const data =
            await response.json();


        console.log(
            "================================="
        );

        console.log(
            "AGENT HISTORY RESPONSE"
        );

        console.log(
            "================================="
        );

        console.log(
            data
        );

        console.log(
            "================================="
        );


        // ------------------------------------------------
        // NO HISTORY
        // ------------------------------------------------

        if (
            !data.messages ||
            !Array.isArray(data.messages) ||
            data.messages.length === 0
        ) {

            console.log(
                "No existing conversation messages."
            );

            return false;
        }


        // ------------------------------------------------
        // RESTORE CONVERSATION AREA
        // ------------------------------------------------

        if (conversationArea) {

            conversationArea.innerHTML = "";

        }


        // ------------------------------------------------
        // RENDER ALL DATABASE MESSAGES
        // ------------------------------------------------

        data.messages.forEach(
            message => {

                if (
                    !message ||
                    !message.role ||
                    !message.content
                ) {

                    return;

                }


                let role =
                    message.role;


                // Backend uses "agent"
                // Frontend uses "assistant"

                if (role === "agent") {

                    role = "assistant";

                }


                addMessageToDOM(
                    role,
                    message.content
                );

            }
        );


        // ------------------------------------------------
        // RESTORE THREAD
        // ------------------------------------------------

        if (
            data.thread_id
        ) {

            threadId =
                data.thread_id;

        }


        // ------------------------------------------------
        // SAVE REQUIREMENTS STATE
        // ------------------------------------------------

        if (data.requirements) {

            console.log(
                "RESTORED REQUIREMENTS:",
                data.requirements
            );

        }


        // ------------------------------------------------
        // NEXT FIELD
        // ------------------------------------------------

        console.log(
            "NEXT INTERVIEW FIELD:",
            data.current_field
        );


        // ------------------------------------------------
        // SCROLL
        // ------------------------------------------------

        scrollConversationToBottom();


        return true;

    }

    catch (error) {

        console.error(
            "LOAD AGENT HISTORY ERROR:",
            error
        );

        return false;

    }

}
// ============================================================
// START INITIAL CONVERSATION
// ============================================================

async function startInitialConversation() {

    console.log("=================================");
    console.log("START INITIAL CONVERSATION");
    console.log("=================================");

    // ------------------------------------------------
    // CHECK PROJECT
    // ------------------------------------------------

    if (!selectedProjectId) {

        console.warn(
            "No project selected."
        );

        return;

    }


    // ------------------------------------------------
    // FALLBACK PROJECT NAME
    // ------------------------------------------------

    if (!selectedProjectName) {

        selectedProjectName =
            localStorage.getItem(
                "selected_project_name"
            ) ||
            "your project";

    }


    console.log(
        "PROJECT ID:",
        selectedProjectId
    );

    console.log(
        "PROJECT NAME:",
        selectedProjectName
    );

    console.log(
        "THREAD ID:",
        threadId
    );


    // ------------------------------------------------
    // CHECK IF WE ALREADY HAVE MESSAGES IN CHAT
    // ------------------------------------------------

    const hasMessages =
        conversationArea &&
        conversationArea.querySelector(
            ".message-content"
        );


    if (hasMessages) {

        console.log(
            "Conversation already contains messages."
        );

        console.log(
            "Skipping /agent/start."
        );

        return;

    }


    // ------------------------------------------------
    // CHECK SESSION STORAGE
    // ------------------------------------------------

    const initialMessageKey =
        `initial_message_${selectedProjectId}_${threadId}`;

    const initialMessageSent =
        sessionStorage.getItem(
            initialMessageKey
        );


    if (initialMessageSent === "true") {

        console.log(
            "Initial conversation already started for this thread."
        );

        console.log(
            "No new /agent/start request."
        );

        return;

    }


    // ------------------------------------------------
    // START AGENT
    // ------------------------------------------------

    isSending = true;

    const typingElement =
        showTypingIndicator();

    updateSendButton(true);


    try {

        console.log(
            "CALLING /agent/start"
        );


        const response =
            await fetch(
                `${API_BASE_URL}/agent/start`,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"

                    },

                    body: JSON.stringify({

                        project_id:
                            Number(selectedProjectId),

                        thread_id:
                            threadId

                    })

                }
            );


        // ------------------------------------------------
        // API ERROR
        // ------------------------------------------------

        if (!response.ok) {

            const errorText =
                await response.text();


            console.error(
                "AGENT START API ERROR:",
                response.status,
                errorText
            );


            throw new Error(
                `Agent start failed (${response.status})`
            );

        }


        // ------------------------------------------------
        // RESPONSE
        // ------------------------------------------------

        const data =
            await response.json();


        console.log(
            "================================="
        );

        console.log(
            "AGENT START RAW RESPONSE"
        );

        console.log(
            "================================="
        );

        console.log(data);

        console.log(
            "JSON:",
            JSON.stringify(
                data,
                null,
                2
            )
        );


        // ------------------------------------------------
        // REMOVE TYPING
        // ------------------------------------------------

        if (typingElement) {

            typingElement.remove();

        }


        // ------------------------------------------------
        // EXTRACT AGENT MESSAGE
        // ------------------------------------------------

        const assistantMessage =
            extractAgentResponse(data);


        console.log(
            "INITIAL AGENT MESSAGE:",
            assistantMessage
        );


        // ------------------------------------------------
        // DISPLAY AGENT MESSAGE
        // ------------------------------------------------

        if (
            assistantMessage &&
            assistantMessage.trim()
        ) {

            addMessage(
                "assistant",
                assistantMessage
            );

        }


        // ------------------------------------------------
        // MARK INITIAL MESSAGE AS SENT
        // ------------------------------------------------

        sessionStorage.setItem(
            initialMessageKey,
            "true"
        );


    }

    catch (error) {

        console.error(
            "START INITIAL CONVERSATION ERROR:",
            error
        );


        // ------------------------------------------------
        // REMOVE TYPING
        // ------------------------------------------------

        if (typingElement) {

            typingElement.remove();

        }


        // ------------------------------------------------
        // SHOW ERROR
        // ------------------------------------------------

        addMessage(
            "assistant",
            "Sorry, I couldn't start the SpecPilot agent. Please try again."
        );

    }

    finally {

        isSending = false;

        updateSendButton(false);

    }

}


// ============================================================
// SEND BUTTON
// ============================================================

if (sendButton) {

    sendButton.addEventListener(
        "click",
        async function (event) {

            event.preventDefault();
            event.stopPropagation();

            console.log(
                "SEND BUTTON CLICKED"
            );

            await sendCurrentMessage();

        }
    );

}


// ============================================================
// ENTER TO SEND
// ============================================================

if (messageInput) {

    messageInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendCurrentMessage();

            }

        }
    );

}


// ============================================================
// SEND CURRENT MESSAGE
// ============================================================

async function sendCurrentMessage() {

    // ------------------------------------------------
    // PREVENT DUPLICATE REQUEST
    // ------------------------------------------------

    if (isSending) {

        return;

    }


    // ------------------------------------------------
    // GET MESSAGE
    // ------------------------------------------------

    const message =
        messageInput?.value?.trim();


    if (!message) {

        return;

    }


    // ------------------------------------------------
    // CHECK PROJECT
    // ------------------------------------------------

    if (!selectedProjectId) {

        alert(
            "Please select a project first."
        );

        return;

    }


    // ------------------------------------------------
    // CLEAR INPUT
    // ------------------------------------------------

    messageInput.value = "";


    // ------------------------------------------------
    // SHOW USER MESSAGE
    // ------------------------------------------------

    addMessage(
        "user",
        message
    );


    // ------------------------------------------------
    // SEND TO AGENT
    // ------------------------------------------------

    await sendMessageToAgent(
        message
    );

}


// ============================================================
// SEND MESSAGE TO BACKEND
// ============================================================
async function sendMessageToAgent(message, initialize = false) {

    console.log("########################################");
    console.log("SEND MESSAGE FUNCTION ENTERED");
    console.log("########################################");
    console.log("MESSAGE:", message);
    console.log("INITIALIZE:", initialize);
    console.log("PROJECT ID:", selectedProjectId);
    console.log("THREAD ID:", threadId);
    console.log("TIME:", new Date().toISOString());


    // ------------------------------------------------
    // PREVENT DUPLICATE REQUEST
    // ------------------------------------------------

    if (isSending) {

        console.warn(
            "MESSAGE SEND BLOCKED: ALREADY SENDING"
        );

        return;

    }


    // ------------------------------------------------
    // CHECK PROJECT
    // ------------------------------------------------

    if (!selectedProjectId) {

        console.error(
            "Cannot send message without project ID."
        );

        return;

    }


    // ------------------------------------------------
    // START LOADING
    // ------------------------------------------------

    isSending = true;

    console.log(
        "STEP 1: isSending = true"
    );


    const typingElement =
        showTypingIndicator();

    console.log(
        "STEP 2: typing indicator created"
    );


    updateSendButton(true);

    console.log(
        "STEP 3: send button disabled"
    );


    try {

        // ------------------------------------------------
        // API REQUEST
        // ------------------------------------------------

        const requestBody = {

            project_id:
                Number(selectedProjectId),

            message:
                message,

            thread_id:
                threadId,

            initialize:
                initialize

        };


        console.log(
            "================================="
        );

        console.log(
            "STEP 4: ABOUT TO CALL /agent/chat"
        );

        console.log(
            "REQUEST BODY:",
            requestBody
        );

        console.log(
            "API URL:",
            `${API_BASE_URL}/agent/chat`
        );

        console.log(
            "================================="
        );


        const response =
            await fetch(
                `${API_BASE_URL}/agent/chat`,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify(requestBody)

                }
            );


        // ------------------------------------------------
        // FETCH COMPLETED
        // ------------------------------------------------

        console.log(
            "STEP 5: FETCH COMPLETED"
        );

        console.log(
            "HTTP STATUS:",
            response.status
        );


        // ------------------------------------------------
        // API ERROR
        // ------------------------------------------------

        if (!response.ok) {

            const errorText =
                await response.text();


            console.error(
                "AGENT API ERROR:",
                response.status,
                errorText
            );


            throw new Error(
                `Agent request failed (${response.status})`
            );

        }


        // ------------------------------------------------
        // READ RESPONSE
        // ------------------------------------------------

        console.log(
            "STEP 6: READING JSON RESPONSE"
        );


        const data =
            await response.json();


        console.log(
            "================================="
        );

        console.log(
            "RAW API RESPONSE"
        );

        console.log(
            "================================="
        );

        console.log(
            data
        );

        // ------------------------------------------------
        // UPDATE PRD BUTTON
        // ------------------------------------------------

        updatePrdButton(data);

        if (
    data?.completeness_status === "COMPLETE" &&
    data?.next_action === "generate_prd" &&
    data?.current_field === null
) {
    lockAgentChat();
}

        console.log(
            "JSON:",
            JSON.stringify(
                data,
                null,
                2
            )
        );

        console.log(
            "================================="
        );


        // ------------------------------------------------
        // REMOVE TYPING
        // ------------------------------------------------

        if (typingElement) {

            typingElement.remove();

        }


        // ------------------------------------------------
        // EXTRACT AGENT MESSAGE
        // ------------------------------------------------

        const assistantMessage =
            extractAgentResponse(data);


        console.log(
            "================================="
        );

        console.log(
            "EXTRACTED AGENT MESSAGE"
        );

        console.log(
            "================================="
        );

        console.log(
            "MESSAGE:",
            assistantMessage
        );

        console.log(
            "TYPE:",
            typeof assistantMessage
        );

        console.log(
            "LENGTH:",
            assistantMessage?.length
        );

        console.log(
            "================================="
        );


        // ------------------------------------------------
        // DISPLAY AGENT RESPONSE
        // ------------------------------------------------

        addMessage(
            "assistant",
            assistantMessage
        );

    }

    catch (error) {

        console.error(
            "SEND MESSAGE ERROR:",
            error
        );


        if (typingElement) {

            typingElement.remove();

        }


        addMessage(
            "assistant",
            "Sorry, I couldn't connect to the SpecPilot agent. Please try again."
        );

    }

    finally {

        isSending = false;

        updateSendButton(false);

        console.log(
            "SEND MESSAGE FUNCTION FINISHED"
        );

    }

}

// ============================================================
// EXTRACT AGENT RESPONSE
// ============================================================

function extractAgentResponse(data) {

    // ------------------------------------------------
    // STRING RESPONSE
    // ------------------------------------------------

    if (typeof data === "string") {

        return data;

    }


    // ------------------------------------------------
    // COMMON RESPONSE FIELDS
    // ------------------------------------------------

    if (data?.response) {

        return data.response;

    }


    if (data?.message) {

        return data.message;

    }


    if (data?.content) {

        return data.content;

    }


    if (data?.answer) {

        return data.answer;

    }


    // ------------------------------------------------
    // MESSAGES ARRAY
    // ------------------------------------------------

    if (
        Array.isArray(data?.messages) &&
        data.messages.length > 0
    ) {

        const lastMessage =
            data.messages[
                data.messages.length - 1
            ];


        if (
            typeof lastMessage ===
            "string"
        ) {

            return lastMessage;

        }


        if (
            lastMessage &&
            lastMessage.content
        ) {

            return lastMessage.content;

        }

    }


    // ------------------------------------------------
    // FALLBACK
    // ------------------------------------------------

    return "I received your request.";

}


// ============================================================
// ADD MESSAGE
// ============================================================

function addMessage(role, message) {

    // ------------------------------------------------
    // SAVE MESSAGE
    // ------------------------------------------------

    saveMessage(
        role,
        message
    );


    // ------------------------------------------------
    // ADD MESSAGE TO DOM
    // ------------------------------------------------

    addMessageToDOM(
        role,
        message
    );

}

// ========================================================
// ADD MESSAGE TO DOM
// ========================================================

function addMessageToDOM(role, message) {

    if (!conversationArea) {
        return;
    }


    // ------------------------------------------------
    // HIDE EMPTY STATE
    // ------------------------------------------------

    if (emptyState) {

        emptyState.style.display =
            "none";

    }


    // ------------------------------------------------
    // CREATE WRAPPER
    // ------------------------------------------------

    const wrapper =
        document.createElement("div");


    // ------------------------------------------------
    // USER MESSAGE
    // ------------------------------------------------

    if (role === "user") {

        wrapper.className =
            "flex justify-end";


        wrapper.innerHTML = `

            <div class="max-w-[75%]">

                <div
                    class="bg-primary-container text-on-primary rounded-xl rounded-br-sm px-4 py-3 shadow-sm"
                >

                    <div
                        class="message-content"
                    ></div>

                </div>

            </div>

        `;

    }


    // ------------------------------------------------
    // ASSISTANT MESSAGE
    // ------------------------------------------------

    else {

        wrapper.className =
            "flex justify-start";


        wrapper.innerHTML = `

            <div class="flex items-start gap-3 max-w-[80%]">

                <div
                    class="w-9 h-9 rounded-full bg-secondary-container text-primary flex items-center justify-center shrink-0"
                >

                    <span
                        class="material-symbols-outlined text-[20px]"
                    >
                        smart_toy
                    </span>

                </div>


                <div>

                    <div
                        class="bg-surface-container-lowest border border-outline-variant rounded-xl rounded-tl-sm px-4 py-3 shadow-sm"
                    >

                        <div
                            class="message-content markdown-content text-on-surface"
                        ></div>

                    </div>

                </div>

            </div>

        `;

    }


    // ------------------------------------------------
    // MESSAGE CONTENT
    // ------------------------------------------------

    const content =
        wrapper.querySelector(
            ".message-content"
        );


    if (content) {

        content.textContent =
            message;

    }


    // ------------------------------------------------
    // ADD TO CHAT
    // ------------------------------------------------

    if (conversationArea) {

        conversationArea.appendChild(
            wrapper
        );

    }


    scrollConversationToBottom();

}


// ============================================================
// TYPING INDICATOR
// ============================================================

function showTypingIndicator() {

    // ------------------------------------------------
    // HIDE EMPTY STATE
    // ------------------------------------------------

    if (emptyState) {

        emptyState.style.display =
            "none";

    }


    // ------------------------------------------------
    // CREATE WRAPPER
    // ------------------------------------------------

    const wrapper =
        document.createElement("div");


    wrapper.className =
        "flex justify-start";


    wrapper.innerHTML = `

        <div class="flex items-start gap-3 max-w-[80%]">

            <div
                class="w-9 h-9 rounded-full bg-secondary-container text-primary flex items-center justify-center shrink-0"
            >

                <span
                    class="material-symbols-outlined text-[20px]"
                >
                    smart_toy
                </span>

            </div>


            <div
                class="bg-surface-container-lowest border border-outline-variant rounded-xl rounded-tl-sm px-5 py-4 shadow-sm"
            >

                <div class="flex gap-1 items-center">

                    <span
                        class="typing-dot w-2 h-2 rounded-full bg-primary"
                    ></span>

                    <span
                        class="typing-dot w-2 h-2 rounded-full bg-primary"
                    ></span>

                    <span
                        class="typing-dot w-2 h-2 rounded-full bg-primary"
                    ></span>

                </div>

            </div>

        </div>

    `;


    if (conversationArea) {

        conversationArea.appendChild(
            wrapper
        );

    }


    scrollConversationToBottom();


    return wrapper;

}

// ============================================================
// CLEAR CONVERSATION BUTTON
// ============================================================

const clearConversationButton =
    document.getElementById(
        "clearConversationButton"
    );


if (clearConversationButton) {

    clearConversationButton.addEventListener(
        "click",
        () => {

            clearConversation();

        }
    );

}

// ============================================================ 
// RESET CONVERSATION UI 
// ============================================================ 
// Used when switching from one project to another.
// IMPORTANT: 
// - Does NOT ask for confirmation. 
// // - Does NOT delete backend conversation history. 
// // - Does NOT remove session storage. 
// // - Only resets what is currently displayed in the chat area. 
// // ============================================================ 
 
function resetConversationUI() { 
    console.log( 
        "RESETTING CONVERSATION UI FOR PROJECT SWITCH" 
    ); 
    // -------------------------------------------------------- 
    // CLEAR CURRENT CHAT DISPLAY 
    // -------------------------------------------------------- 
    if (conversationArea) {
         conversationArea.innerHTML = ""; 
        } 
    // -------------------------------------------------------- 
    // CREATE FRESH EMPTY STATE 
    // -------------------------------------------------------- 
    const newEmptyState = createEmptyState(); 
    // -------------------------------------------------------- 
    // ADD EMPTY STATE TO CHAT 
    // --------------------------------------------------------
    if (conversationArea) { 
        conversationArea.appendChild( newEmptyState );
     } 
     // -------------------------------------------------------- 
     // RESET PRD BUTTON 
     // -------------------------------------------------------- 
     if (generatePrdButton) { 
         generatePrdButton.classList.add( "hidden" ); 
        } 
    console.log( "CONVERSATION UI RESET COMPLETE" );
 }
// ============================================================
 // CLEAR CONVERSATION 
// ============================================================
 function clearConversation()
 { 
// ------------------------------------------------ 
// CONFIRMATION 
// ------------------------------------------------ 
const confirmed = window.confirm
( "Do you want to clear the whole chat?" ); 
// ------------------------------------------------ 
// USER CANCELLED 
// ------------------------------------------------ 
if (!confirmed) {
 console.log
( "CLEAR CHAT CANCELLED" ); 
return; }
 // ------------------------------------------------
 // CLEAR CHAT FROM UI 
// ------------------------------------------------ 
if (conversationArea) 
{
 conversationArea.innerHTML = "";
 }
 // ------------------------------------------------ 
// CLEAR SESSION STORAGE CHAT 
// ------------------------------------------------ 
const conversationKey =
 getConversationStorageKey(); 
if (conversationKey) 
{ 
sessionStorage.removeItem( conversationKey ); 
}
 // ------------------------------------------------ 
// CLEAR INITIAL MESSAGE FLAG 
// ------------------------------------------------ if (selectedProjectId && threadId) { const initialMessageKey = `initial_message_${selectedProjectId}_${threadId}`; sessionStorage.removeItem( initialMessageKey ); } // ------------------------------------------------ // SHOW EMPTY STATE // ------------------------------------------------ const newEmptyState = createEmptyState(); if (conversationArea) { conversationArea.appendChild( newEmptyState ); } console.log( "=================================" ); console.log( "WHOLE CHAT CLEARED" ); console.log( "PROJECT:", selectedProjectId ); console.log( "THREAD:", threadId ); console.log( "=================================" ); }
if (selectedProjectId && threadId){ 
    const initialMessageKey = 
    `initial_message_${selectedProjectId}_${threadId}`;
     
    sessionStorage.removeItem( 
        initialMessageKey 
    ); 
} 
// ------------------------------------------------ 
//  SHOW EMPTY STATE 
// ------------------------------------------------ 
const newEmptyState = 
createEmptyState(); 
if (conversationArea) { 
    conversationArea.appendChild( 
        newEmptyState 
    ); 
} 
console.log( 
    "=================================" );
     console.log( "WHOLE CHAT CLEARED" ); 
     
     console.log( "PROJECT:", selectedProjectId ); 
     console.log( "THREAD:", threadId ); 
     
     console.log( "=================================" );
 }


// ============================================================
// CREATE EMPTY STATE
// ============================================================

function createEmptyState() {

    const div =
        document.createElement("div");


    div.id =
        "emptyState";


    div.className =
        "flex-1 flex items-center justify-center";


    div.innerHTML = `

        <div class="text-center max-w-lg">

            <div
                class="w-16 h-16 mx-auto mb-5 rounded-full bg-secondary-container flex items-center justify-center text-primary"
            >

                <span
                    class="material-symbols-outlined text-[32px]"
                >
                    smart_toy
                </span>

            </div>


            <h3
                class="font-headline-md text-headline-md font-semibold text-on-surface mb-2"
            >
                Start a conversation
            </h3>


            <p
                class="text-on-surface-variant"
            >
                Select a project and ask SpecPilot about requirements, architecture, implementation, or project planning.
            </p>

        </div>

    `;


    return div;

}


// ============================================================
// SCROLL CONVERSATION
// ============================================================

function scrollConversationToBottom() {

    if (!conversationArea) {

        return;

    }


    conversationArea.scrollTo({

        top:
            conversationArea.scrollHeight,

        behavior:
            "smooth"

    });

}


// ============================================================
// SEND BUTTON STATE
// ============================================================

function updateSendButton(loading) {

    if (!sendButton) {

        return;

    }


    if (loading) {

        sendButton.disabled =
            true;


        if (sendIcon) {

            sendIcon.textContent =
                "progress_activity";


            sendIcon.classList.add(
                "animate-spin"
            );

        }

    }

    else {

        sendButton.disabled =
            false;


        if (sendIcon) {

            sendIcon.textContent =
                "send";


            sendIcon.classList.remove(
                "animate-spin"
            );

        }

    }

}
});
