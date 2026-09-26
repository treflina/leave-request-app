const dialogPreviousFocus = new WeakMap();

const focusableSelector = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
].join(",");

const focusDialog = (dialog) => {
    const labelledBy = dialog.getAttribute("aria-labelledby");
    const heading = labelledBy
        ? document.getElementById(labelledBy)
        : null;
    const focusable = dialog.querySelector(focusableSelector);

    if (heading) {
        heading.setAttribute("tabindex", "-1");
    }

    (heading || focusable || dialog).focus();
};

document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[onclick]");

    if (!trigger) {
        return;
    }

    const match = trigger.getAttribute("onclick").match(
        /getElementById\(['"]([^'"]+)['"]\)\.showModal\(\)/
    );

    if (!match) {
        return;
    }

    const dialog = document.getElementById(match[1]);

    if (!dialog) {
        return;
    }

    dialogPreviousFocus.set(dialog, trigger);
    requestAnimationFrame(() => focusDialog(dialog));
}, true);

document.querySelectorAll("dialog").forEach((dialog) => {
    dialog.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            event.preventDefault();
            dialog.close();
            return;
        }

        if (event.key !== "Tab") {
            return;
        }

        const focusable = Array.from(
            dialog.querySelectorAll(focusableSelector)
        );

        if (focusable.length === 0) {
            event.preventDefault();
            dialog.focus();
            return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    });

    dialog.addEventListener("close", () => {
        const previousFocus = dialogPreviousFocus.get(dialog);

        if (previousFocus && document.contains(previousFocus)) {
            previousFocus.focus();
        }
    });
});