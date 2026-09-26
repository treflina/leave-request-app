const skipLink = document.querySelector(".skip-link");

if (skipLink) {
    skipLink.addEventListener("click", (event) => {
        const main = document.querySelector("#main-content main");

        if (!main) {
            return;
        }

        event.preventDefault();
        main.setAttribute("tabindex", "-1");
        main.focus({ preventScroll: true });
        main.scrollIntoView({ block: "start" });
        history.replaceState(null, "", "#main-content");
    });
}