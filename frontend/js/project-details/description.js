// =========================================================
// DESCRIPTION RENDERER
// =========================================================

import {
    setContent
} from "./utils.js";


// =========================================================
// HELPER
// =========================================================

function hasValue(value) {

    return (
        value !== null &&
        value !== undefined &&
        String(value).trim() !== ""
    );
}


// =========================================================
// RENDER DESCRIPTION
// =========================================================

export function renderDescription(project) {

    if (
        !project ||
        typeof project !== "object"
    ) {
        project = {};
    }


    // -----------------------------------------------------
    // SUPPORT BOTH:
    //
    // 1. Original database project
    // 2. AI generated description
    // -----------------------------------------------------

    const description =
        project.description &&
        typeof project.description === "object"
            ? project.description
            : project;


    // -----------------------------------------------------
    // OVERVIEW
    // -----------------------------------------------------

    setContent(
        "overviewContent",
        hasValue(description.overview)
            ? description.overview
            : project.business_objective
    );


    // -----------------------------------------------------
    // PROBLEM STATEMENT
    // -----------------------------------------------------

    setContent(
        "problemStatementContent",
        hasValue(description.problem_statement)
            ? description.problem_statement
            : project.problem_statement
    );


    // -----------------------------------------------------
    // PROPOSED SOLUTION
    // -----------------------------------------------------

    setContent(
        "solutionContent",
        hasValue(description.proposed_solution)
            ? description.proposed_solution
            : project.proposed_solution
    );


    // -----------------------------------------------------
    // TARGET AUDIENCE
    // -----------------------------------------------------

    setContent(
        "targetAudienceContent",
        hasValue(description.target_audience)
            ? description.target_audience
            : project.target_users
    );


    // -----------------------------------------------------
    // BUSINESS VALUE
    // -----------------------------------------------------

    setContent(
        "businessValueContent",
        hasValue(description.business_value)
            ? description.business_value
            : project.business_value ||
              project.business_objective
    );


    // -----------------------------------------------------
    // MAJOR FEATURES
    // -----------------------------------------------------

    setContent(
        "majorFeaturesContent",
        hasValue(description.major_features)
            ? description.major_features
            : project.expected_features
    );


    // -----------------------------------------------------
    // EXPECTED OUTCOME
    // -----------------------------------------------------

    setContent(
        "expectedOutcomeContent",
        hasValue(description.expected_outcome)
            ? description.expected_outcome
            : project.expected_outcome ||
              project.additional_instructions
    );
}