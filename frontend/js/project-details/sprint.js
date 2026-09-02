// =========================================================
// SPRINT PLAN RENDERER
// =========================================================

import {
    setContent
} from "./utils.js";


export function renderSprint(sprintPlan) {

    if (
        typeof sprintPlan === "object" &&
        sprintPlan !== null
    ) {

        sprintPlan =
            JSON.stringify(
                sprintPlan,
                null,
                2
            );
    }


    setContent(
        "sprintContent",
        sprintPlan
    );
}
