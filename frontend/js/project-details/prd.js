// =========================================================
// PRD RENDERER
// =========================================================

import {
    parseJSONIfPossible,
    setContent
} from "./utils.js";


// =========================================================
// RENDER PRD
// =========================================================

export function renderPRD(source) {

    let prd = source?.prd;

    // If PRD exists separately, parse it
    if (typeof prd === "string") {
        prd = parseJSONIfPossible(prd);
    }

    // If there is no separate PRD object,
    // use the source itself
    if (
        !prd ||
        typeof prd !== "object" ||
        Array.isArray(prd)
    ) {
        prd = source || {};
    }


    setContent(
        "prdProductOverview",
        prd.product_overview
    );

    setContent(
        "prdGoals",
        prd.goals_and_objectives
    );

    setContent(
        "prdTargetUsers",
        prd.target_users
    );

    setContent(
        "prdFunctionalRequirements",
        prd.functional_requirements
    );

    setContent(
        "prdUserWorkflows",
        prd.user_workflows
    );

    setContent(
        "prdBusinessRules",
        prd.business_rules
    );

    setContent(
        "prdNonFunctionalRequirements",
        prd.non_functional_requirements
    );

    setContent(
        "prdAssumptions",
        prd.assumptions_and_dependencies
    );

    setContent(
        "prdAcceptanceCriteria",
        prd.acceptance_criteria
    );
}
