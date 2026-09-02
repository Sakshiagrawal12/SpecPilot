// =========================================================
// PROJECT DETAILS UTILITIES
// =========================================================


// =========================================================
// PARSE JSON SAFELY
// =========================================================

export function parseJSONIfPossible(value) {

    if (typeof value !== "string") {
        return value;
    }

    try {

        return JSON.parse(value);

    } catch (error) {

        console.warn(
            "Value is not valid JSON:",
            value
        );

        return value;
    }
}


// =========================================================
// ESCAPE HTML
// =========================================================

export function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)

        .replace(/&/g, "&amp;")

        .replace(/</g, "&lt;")

        .replace(/>/g, "&gt;")

        .replace(/"/g, "&quot;")

        .replace(/'/g, "&#039;");
}


// =========================================================
// SET TEXT
// =========================================================

export function setText(elementId, value) {

    const element =
        document.getElementById(elementId);

    if (!element) {

        console.warn(
            "Text element not found:",
            elementId
        );

        return;
    }

    element.textContent =
        value !== null &&
        value !== undefined &&
        value !== ""
            ? String(value)
            : "Not available.";
}


// =========================================================
// SET CONTENT
// =========================================================

export function setContent(elementId, value) {

    const element =
        document.getElementById(elementId);

    if (!element) {

        console.warn(
            "Element not found:",
            elementId
        );

        return;
    }


    // -----------------------------------------------------
    // EMPTY VALUE
    // -----------------------------------------------------

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        element.innerHTML = `
            <div class="empty-content">
                Content not generated yet.
            </div>
        `;

        return;
    }


    // -----------------------------------------------------
    // ARRAY
    // -----------------------------------------------------

    if (Array.isArray(value)) {

        element.innerHTML = `

            <ul class="list-disc pl-6 space-y-2">

                ${value
                    .map(item => {

                        if (
                            typeof item === "object" &&
                            item !== null
                        ) {

                            return `
                                <li>
                                    ${escapeHtml(
                                        JSON.stringify(
                                            item,
                                            null,
                                            2
                                        )
                                    )}
                                </li>
                            `;
                        }

                        return `
                            <li>
                                ${escapeHtml(item)}
                            </li>
                        `;

                    })
                    .join("")
                }

            </ul>
        `;

        return;
    }


    // -----------------------------------------------------
    // OBJECT
    // -----------------------------------------------------

    if (typeof value === "object") {

        element.innerHTML = `

            <pre class="
                whitespace-pre-wrap
                text-sm
            ">${escapeHtml(
                JSON.stringify(
                    value,
                    null,
                    2
                )
            )}</pre>

        `;

        return;
    }


    // -----------------------------------------------------
    // STRING
    // -----------------------------------------------------

    element.innerHTML =
        escapeHtml(String(value))
            .replace(/\r?\n/g, "<br>");
}
