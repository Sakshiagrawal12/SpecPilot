// ========================================================= 
//  PRD RENDERER 
// ========================================================= 

import { parseJSONIfPossible, setContent } from "./utils.js"; 

// Must match the API_URL used in project-details.js — without this,
// fetch() below resolves against whatever origin is serving this HTML
// file (e.g. a static file server), not the FastAPI backend, and the
// request 404s.
const API_URL = "http://127.0.0.1:8000";

let currentWorkflowText = "";
let currentMermaidCode = "";

let isDiagramView = false;

// ========================================================= 
// // RENDER PRD 
// // ========================================================= 
export function renderPRD(source) 
{ console.log( "=================================" ); 
    console.log( "RENDERING PRD" ); 
    console.log( "=================================" ); 
    let prd = source?.prd; 
    // ----------------------------------------------------- 
    // // If PRD is stored as a JSON string 
    // // ----------------------------------------------------- 
    // 
    if (typeof prd === "string") 
        { prd = parseJSONIfPossible(prd); } 
    
    // ----------------------------------------------------- 
    // // If there is no separate PRD object, // use the source itself 
    // // ----------------------------------------------------- 
    // 
    if ( !prd || typeof prd !== "object" || Array.isArray(prd) ) 
        { prd = source || {}; } 
    console.log( "PRD DATA:", prd ); 
    // ----------------------------------------------------- 
    // // PRODUCT OVERVIEW 
    // // ----------------------------------------------------- 
    // 
    setContent( "prdProductOverview", prd.product_overview ); 
    
    // ----------------------------------------------------- 
    // // PROBLEM STATEMENT 
    // // ----------------------------------------------------- 
    
    setContent( "prdProblemStatement", prd.problem_statement ); 
    
    // ----------------------------------------------------- 
    // // GOALS AND OBJECTIVES
    //  // ----------------------------------------------------- 
    // 
    setContent( "prdGoals", prd.goals_and_objectives ); 
    
    // ----------------------------------------------------- 
    // // TARGET USERS 
    // // ----------------------------------------------------- 
     setContent( "prdTargetUsers", prd.target_users ); 
     
     // ----------------------------------------------------- 
     // // FUNCTIONAL REQUIREMENTS 
     // // ----------------------------------------------------- 
     // 
     setContent( "prdFunctionalRequirements", prd.functional_requirements ); 
     
     // -----------------------------------------------------
     //  // BUSINESS RULES 
     // // ----------------------------------------------------- 
     // 
     setContent( "prdBusinessRules", prd.business_rules ); 
     // ----------------------------------------------------- 
     // // NON-FUNCTIONAL REQUIREMENTS 
     // // ----------------------------------------------------- 
     // 
     setContent( "prdNonFunctionalRequirements", prd.non_functional_requirements );
      // ----------------------------------------------------- 
      // // ASSUMPTIONS AND DEPENDENCIES 
      // // ----------------------------------------------------- 
      // 
      setContent( "prdAssumptions", prd.assumptions_and_dependencies ); 
      
      // ----------------------------------------------------- 
      // // ACCEPTANCE CRITERIA 
      // // ----------------------------------------------------- 
      // 
      setContent( "prdAcceptanceCriteria", prd.acceptance_criteria ); 
      console.log( "PRD RENDERING COMPLETE" ); 
    
       // ----------------------------------------------------- 
     // // USER WORKFLOWS // 
     // ----------------------------------------------------- 
     // 
     setupWorkflowSection(
        prd.user_workflows
    );


    console.log("PRD RENDERING COMPLETE");
}
    // =========================================================
// SETUP USER WORKFLOW SECTION
// =========================================================

function setupWorkflowSection(rawWorkflow) {

    const textElement =
        document.getElementById(
            "prdUserWorkflows"
        );

    const diagramElement =
        document.getElementById(
            "prdUserWorkflowsDiagram"
        );

    const convertBtn =
        document.getElementById(
            "convertWorkflowDiagramBtn"
        );

    const convertBtnText =
        document.getElementById(
            "convertBtnText"
        );


    console.log(
        "WORKFLOW:",
        rawWorkflow
    );

    console.log(
        "BUTTON:",
        convertBtn
    );


    if (!textElement) {

        console.error(
            "prdUserWorkflows element not found"
        );

        return;
    }


    if (!diagramElement) {

        console.error(
            "prdUserWorkflowsDiagram element not found"
        );

        return;
    }


    if (!convertBtn) {

        console.error(
            "convertWorkflowDiagramBtn not found"
        );

        return;
    }


    // =====================================================
    // NO WORKFLOW
    // =====================================================

    if (!rawWorkflow) {

        textElement.innerHTML = `
            <div class="empty-content">
                Content not generated yet.
            </div>
        `;

        convertBtn.classList.add(
            "hidden"
        );

        return;
    }


    // =====================================================
    // STORE WORKFLOW
    // =====================================================

    currentWorkflowText =
        String(rawWorkflow);

    currentMermaidCode = "";

    isDiagramView = false;


    // =====================================================
    // SHOW WORKFLOW TEXT
    // =====================================================

    textElement.innerHTML =
        window.marked
            ? window.marked.parse(
                currentWorkflowText
            )
            : currentWorkflowText;


    // =====================================================
    // INITIAL VIEW
    // =====================================================

    textElement.classList.remove(
        "hidden"
    );

    diagramElement.classList.add(
        "hidden"
    );

    diagramElement.innerHTML = "";


    // =====================================================
    // SHOW BUTTON
    // =====================================================

    convertBtn.classList.remove(
        "hidden"
    );


    if (convertBtnText) {

        convertBtnText.textContent =
            "Convert to Diagram";
    }


    // =====================================================
    // PREVENT DUPLICATE LISTENERS
    // =====================================================

    const newBtn =
        convertBtn.cloneNode(true);

    convertBtn.parentNode.replaceChild(
        newBtn,
        convertBtn
    );


    newBtn.addEventListener(
        "click",
        handleDiagramToggle
    );
}


// =========================================================
// HANDLE TEXT / DIAGRAM TOGGLE
// =========================================================

async function handleDiagramToggle() {

    const textElement =
        document.getElementById(
            "prdUserWorkflows"
        );

    const diagramElement =
        document.getElementById(
            "prdUserWorkflowsDiagram"
        );

    const convertBtnText =
        document.getElementById(
            "convertBtnText"
        );


    // =====================================================
    // DIAGRAM → TEXT
    // =====================================================

    if (isDiagramView) {

        diagramElement.classList.add(
            "hidden"
        );

        textElement.classList.remove(
            "hidden"
        );


        convertBtnText.textContent =
            "Convert to Diagram";


        isDiagramView = false;

        return;
    }


    // =====================================================
    // TEXT → DIAGRAM
    // =====================================================

    textElement.classList.add(
        "hidden"
    );

    diagramElement.classList.remove(
        "hidden"
    );


    convertBtnText.textContent =
        "View Step-by-Step Text";


    isDiagramView = true;


    // =====================================================
    // SHOW LOADING
    // =====================================================

    diagramElement.innerHTML = `
        <div class="flex items-center gap-2 text-sm py-4">

            <span class="material-symbols-outlined animate-spin">
                progress_activity
            </span>

            Generating workflow diagram...

        </div>
    `;


    try {

        // =================================================
        // CALL DIAGRAM AGENT
        // =================================================

        const accessToken =
            localStorage.getItem(
                "access_token"
            );

        const response = await fetch(
            `${API_URL}/agent/convert-workflow-diagram`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                    "Authorization":
                        `Bearer ${accessToken}`
                },

                body: JSON.stringify({

                    workflow_text:
                        currentWorkflowText

                })
            }
        );


        if (!response.ok) {

            throw new Error(
                `Diagram API failed: ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log(
            "DIAGRAM RESPONSE:",
            data
        );


        // =================================================
        // SAVE MERMAID
        // =================================================

        currentMermaidCode =
            data.mermaid_code;


        // =================================================
        // RENDER
        // =================================================

        await renderMermaidDiagram(
            diagramElement,
            currentMermaidCode
        );


    }

    catch (error) {

        console.error(
            "DIAGRAM GENERATION ERROR:",
            error
        );


        diagramElement.innerHTML = `
            <div class="text-sm py-2">
                Failed to generate workflow diagram.
            </div>
        `;
    }
}

// =========================================================
// RENDER MERMAID DIAGRAM
// =========================================================

async function renderMermaidDiagram(
    container,
    mermaidCode
) {

    try {

        if (!window.mermaid) {

            throw new Error(
                "Mermaid.js is not loaded."
            );
        }


        const diagramId =
            `workflow-diagram-${Date.now()}`;


        container.innerHTML = `
            <div
                id="${diagramId}"
                class="mermaid"
            >
${mermaidCode}
            </div>
        `;


        await window.mermaid.run({
            nodes:
                container.querySelectorAll(
                    ".mermaid"
                )
        });


    }

    catch (error) {

        console.error(
            "MERMAID RENDER ERROR:",
            error
        );


        container.innerHTML = `
            <div class="text-sm py-2">
                Unable to render workflow diagram.
            </div>

            <pre class="mt-2 p-3 rounded text-xs overflow-x-auto">${mermaidCode}</pre>
        `;
    }
}