const settingsDialog =
    document.getElementById("settingsModal");

const settingsOpenButton =
    document.getElementById("settings-open-btn");

const settingsCloseButton =
    document.getElementById("settings-close-btn");

const settingsHeading =
    document.getElementById("settingsModalLabel");

let settingsPreviousFocus = null;


if (
    settingsDialog &&
    settingsOpenButton &&
    settingsCloseButton &&
    settingsHeading
) {
    settingsOpenButton.addEventListener("click", () => {
        settingsPreviousFocus = document.activeElement;

        settingsDialog.showModal();

        requestAnimationFrame(() => {
            settingsHeading.focus();
        });
    });


    settingsCloseButton.addEventListener("click", () => {
        settingsDialog.close();
    });


    settingsDialog.addEventListener("click", (event) => {
        if (event.target === settingsDialog) {
            settingsDialog.close();
        }
    });


    settingsDialog.addEventListener("close", () => {
        if (settingsPreviousFocus) {
            settingsPreviousFocus.focus();
        }
    });


    settingsDialog.addEventListener("keydown", (event) => {
        if (event.key !== "Tab") {
            return;
        }

        const focusableElements =
            settingsDialog.querySelectorAll(
                'a[href], button:not([disabled]), ' +
                'input:not([disabled]), ' +
                'select:not([disabled]), ' +
                'textarea:not([disabled]), ' +
                '[tabindex]:not([tabindex="-1"])'
            );

        const focusable =
            Array.from(focusableElements);

        if (focusable.length === 0) {
            event.preventDefault();
            settingsHeading.focus();
            return;
        }

        const firstElement = focusable[0];
        const lastElement =
            focusable[focusable.length - 1];


        if (
            event.shiftKey &&
            document.activeElement === firstElement
        ) {
            event.preventDefault();
            lastElement.focus();
        }


        if (
            !event.shiftKey &&
            document.activeElement === lastElement
        ) {
            event.preventDefault();
            firstElement.focus();
        }
    });
}

