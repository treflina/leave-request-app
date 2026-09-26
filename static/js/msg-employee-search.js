document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.querySelector("[data-employee-search]");

    if (!searchInput) {
        return;
    }

    const employeeRows = Array.from(
        document.querySelectorAll("[data-employee-row]")
    );

    const noResults = document.querySelector("[data-no-results]");
    const searchStatus = document.querySelector("[data-search-status]");
    const resultCount = document.querySelector("[data-result-count]");

    function updateSearch() {
        const query = searchInput.value
            .toLowerCase()
            .trim();

        let visibleCount = 0;

        employeeRows.forEach(function (row) {
            const name = row.dataset.name || "";
            const matches = name.includes(query);

            row.classList.toggle("hidden", !matches);

            if (matches) {
                visibleCount++;
            }
        });

        if (noResults) {
            noResults.classList.toggle(
                "hidden",
                visibleCount !== 0
            );
        }

        if (resultCount) {
            resultCount.textContent =
                query === ""
                    ? `${visibleCount} pracowników`
                    : `${visibleCount} wyników`;
        }

        if (searchStatus) {
            if (query === "") {
                searchStatus.textContent =
                    `Wyświetlono wszystkich ${visibleCount} odbiorców.`;
            } else if (visibleCount === 0) {
                searchStatus.textContent =
                    "Nie znaleziono pracowników pasujących do wyszukiwania.";
            } else {
                searchStatus.textContent =
                    `Znaleziono ${visibleCount} odbiorców.`;
            }
        }
    }

    searchInput.addEventListener("input", updateSearch);

    updateSearch();
});
