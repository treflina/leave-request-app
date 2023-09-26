const dropdown = document.getElementById("id_dropdown_field");
dropdown.addEventListener("change", function () {
    document.querySelector(".filter-dropdown-form").submit();
});
