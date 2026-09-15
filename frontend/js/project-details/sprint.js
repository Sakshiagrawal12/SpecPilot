// =========================================================
// SPRINT PLAN RENDERER
// =========================================================

export function renderSprint(sprintPlan) {

    if (
        typeof sprintPlan === "object" &&
        sprintPlan !== null
    ) {

        sprintPlan = JSON.stringify(
            sprintPlan,
            null,
            2
        );
    }

    const container = document.getElementById("sprintContent");

    if (!container) {
        return;
    }

    if (
        !sprintPlan ||
        typeof sprintPlan !== "string" ||
        !sprintPlan.trim()
    ) {

        container.innerHTML = `
            <div class="empty-content">
                Content not generated yet.
            </div>
        `;

        return;
    }

    if (typeof marked === "undefined") {

        console.error(
            "marked.js is not loaded — check the script tag in project-details.html"
        );

        container.textContent = sprintPlan;

        return;
    }

    container.innerHTML = marked.parse(sprintPlan);
}