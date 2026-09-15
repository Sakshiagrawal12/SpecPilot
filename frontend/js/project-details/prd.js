// ========================================================= 
//  PRD RENDERER 
// ========================================================= 

import { parseJSONIfPossible, setContent } from "./utils.js"; 
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
     // // USER WORKFLOWS // 
     // ----------------------------------------------------- 
     // 
     setContent( "prdUserWorkflows", prd.user_workflows ); 
     
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
    
    }

