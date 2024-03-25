const navList = document.querySelector(".navbar-collapse");

document.addEventListener("click", (e) => {
    if (e.target !== navList) {
        navList.classList.remove("show");
    }
});
