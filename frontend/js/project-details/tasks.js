// =========================================================
// TASKS
// =========================================================

import {
    escapeHtml,
    parseJSONIfPossible
} from "./utils.js";


// =========================================================
// DISPLAY TASKS
// =========================================================

export function displayTasks(tasks) {

    const container =
        document.getElementById(
            "tasksContainer"
        );


    const noTasks =
        document.getElementById(
            "noTasks"
        );


    if (!container) {

        console.warn(
            "tasksContainer element not found."
        );

        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(tasks) ||
        tasks.length === 0
    ) {

        if (noTasks) {

            noTasks.classList.remove(
                "hidden"
            );
        }

        return;
    }


    if (noTasks) {

        noTasks.classList.add(
            "hidden"
        );
    }


    tasks.forEach(
        function (task, index) {

            const card =
                createTaskCard(
                    task,
                    index
                );


            container.appendChild(
                card
            );
        }
    );
}


// =========================================================
// CREATE TASK CARD
// =========================================================

function createTaskCard(task, index) {

    const card =
        document.createElement(
            "div"
        );


    card.className =
        "bg-surface-container-lowest " +
        "border border-outline-variant " +
        "rounded-xl p-6 " +
        "hover:shadow-md transition";


    const title =
        task.task_title ||
        task.title ||
        task.task_name ||
        task.name ||
        `Task ${index + 1}`;


    const description =
        task.description ||
        "";


    const status =
        task.status ||
        "Todo";


    const priority =
        task.priority ||
        "Medium";


    const module =
        task.module ||
        task.category ||
        "General";


    const complexity =
        task.estimated_complexity ||
        task.complexity ||
        task.complexity_score ||
        "-";


    const owner =
        task.owner_role ||
        task.assignee ||
        task.owner ||
        "Unassigned";


    let criteria =
        task.acceptance_criteria ||
        [];


    // -----------------------------------------------------
    // NORMALIZE ACCEPTANCE CRITERIA
    // -----------------------------------------------------

    if (typeof criteria === "string") {

        criteria =
            parseJSONIfPossible(
                criteria
            );
    }


    if (!Array.isArray(criteria)) {

        criteria =
            criteria
                ? [criteria]
                : [];
    }


    card.innerHTML = `

        <div class="
            flex flex-col
            lg:flex-row
            lg:items-start
            lg:justify-between
            gap-4
        ">

            <div class="flex gap-4">

                <button
                    type="button"
                    class="
                        task-check
                        w-6 h-6
                        rounded-md
                        border
                        border-outline-variant
                        flex
                        items-center
                        justify-center
                        flex-shrink-0
                    "
                >

                    <span
                        class="
                            material-symbols-outlined
                            text-sm
                            hidden
                        "
                    >
                        check
                    </span>

                </button>


                <div>

                    <h3
                        class="
                            text-xl
                            font-semibold
                            font-headline
                        "
                    >
                        ${escapeHtml(title)}
                    </h3>


                    <p
                        class="
                            mt-2
                            text-sm
                            text-on-surface-variant
                        "
                    >
                        ${escapeHtml(description)}
                    </p>


                    <div
                        class="
                            flex
                            flex-wrap
                            gap-2
                            mt-4
                        "
                    >

                        <span
                            class="
                                px-3 py-1
                                rounded-full
                                bg-secondary-container
                                text-primary
                                text-xs
                                font-semibold
                            "
                        >
                            ${escapeHtml(module)}
                        </span>


                        <span
                            class="
                                px-3 py-1
                                rounded-full
                                bg-surface-container-high
                                text-xs
                            "
                        >
                            ${escapeHtml(status)}
                        </span>


                        <span
                            class="
                                px-3 py-1
                                rounded-full
                                bg-surface-container-high
                                text-xs
                            "
                        >
                            ${escapeHtml(priority)}
                        </span>

                    </div>

                </div>

            </div>


            <div
                class="
                    text-sm
                    text-on-surface-variant
                "
            >

                <div>
                    <strong>Owner:</strong>
                    ${escapeHtml(owner)}
                </div>

                <div class="mt-1">
                    <strong>Complexity:</strong>
                    ${escapeHtml(complexity)}
                </div>

            </div>

        </div>


        ${
            criteria.length > 0

                ? `

                <div
                    class="
                        mt-6
                        pt-5
                        border-t
                        border-outline-variant
                    "
                >

                    <h4
                        class="
                            font-semibold
                            flex
                            items-center
                            gap-2
                            mb-3
                        "
                    >

                        <span
                            class="
                                material-symbols-outlined
                                text-primary
                            "
                        >
                            rule
                        </span>

                        Acceptance Criteria

                    </h4>


                    <ul class="space-y-2">

                        ${criteria
                            .map(
                                criterion => {

                                    if (
                                        typeof criterion === "object" &&
                                        criterion !== null
                                    ) {

                                        criterion =
                                            JSON.stringify(
                                                criterion
                                            );
                                    }


                                    return `

                                        <li
                                            class="
                                                flex
                                                items-start
                                                gap-2
                                                text-sm
                                                text-on-surface-variant
                                            "
                                        >

                                            <span
                                                class="
                                                    material-symbols-outlined
                                                    text-primary
                                                    text-base
                                                "
                                            >
                                                radio_button_unchecked
                                            </span>

                                            <span>
                                                ${escapeHtml(
                                                    criterion
                                                )}
                                            </span>

                                        </li>

                                    `;
                                }
                            )
                            .join("")
                        }

                    </ul>

                </div>

                `

                : ""
        }

    `;


    // =====================================================
    // TASK CHECKBOX
    // =====================================================

    const checkbox =
        card.querySelector(
            ".task-check"
        );


    if (checkbox) {

        checkbox.addEventListener(
            "click",
            function () {

                checkbox.classList.toggle(
                    "bg-primary"
                );


                checkbox.classList.toggle(
                    "text-white"
                );


                const icon =
                    checkbox.querySelector(
                        "span"
                    );


                if (icon) {

                    icon.classList.toggle(
                        "hidden"
                    );
                }
            }
        );
    }


    return card;
}
