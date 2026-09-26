document.addEventListener("DOMContentLoaded", function () {
    const employeeList = document.getElementById("employee-list");
    const selectAllButton = document.getElementById("select-all");
    const clearAllButton = document.getElementById("clear-all");
    const selectedCount = document.getElementById("selected-count");

    if (
        !employeeList ||
        !selectAllButton ||
        !clearAllButton ||
        !selectedCount
    ) {
        return;
    }

    const checkboxes = Array.from(
        employeeList.querySelectorAll(
            'input[type="checkbox"]'
        )
    );

    function updateSelectedCount() {
        const count = checkboxes.filter(function (checkbox) {
            return checkbox.checked;
        }).length;

        selectedCount.textContent = count;
    }

    selectAllButton.addEventListener("click", function () {
        checkboxes.forEach(function (checkbox) {
            const row = checkbox.closest("[data-employee-row]");

            if (!row || !row.classList.contains("hidden")) {
                checkbox.checked = true;
            }
        });

        updateSelectedCount();
    });

    clearAllButton.addEventListener("click", function () {
        checkboxes.forEach(function (checkbox) {
            checkbox.checked = false;
        });

        updateSelectedCount();
    });

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener(
            "change",
            updateSelectedCount
        );
    });

    updateSelectedCount();
});
