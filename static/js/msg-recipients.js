document.addEventListener("DOMContentLoaded", function () {
    const selectedCount = document.getElementById(
        "selected-count"
    );

    const removeButton = document.getElementById(
        "remove-selected"
    );

    const checkboxes = Array.from(
        document.querySelectorAll(
            ".employee-remove-checkbox"
        )
    );

    if (
        !selectedCount ||
        !removeButton ||
        checkboxes.length === 0
    ) {
        return;
    }

    function updateSelectedCount() {
        const count = checkboxes.filter(function (checkbox) {
            return checkbox.checked;
        }).length;

        removeButton.disabled = count === 0;

        if (count === 0) {
            selectedCount.textContent =
                "Nie zaznaczono pracowników";
        } else {
            selectedCount.textContent =
                `Zaznaczono: ${count}`;
        }
    }

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener(
            "change",
            updateSelectedCount
        );
    });

    updateSelectedCount();
});
