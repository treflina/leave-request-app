document.addEventListener("DOMContentLoaded", function () {
    const workDateInput = document.querySelector("#id_work_date");
    const radios = document.querySelectorAll('input[name="leave_type"]');
    const boxW = document.querySelector(".box_w");
    const boxWS = document.querySelector(".box_ws");

    if (!radios.length || !boxW || !boxWS) return;

    const updateUI = (value) => {
        boxW.classList.add("hide");
        boxWS.classList.add("hide");

        if (value === "W") {
            boxW.classList.remove("hide");
        } else if (value === "WS" || value === "WN") {
            boxWS.classList.remove("hide");
        }
        if (value === "W" && workDateInput) {
            workDateInput.value = "";
        }
    };

    const checked = document.querySelector('input[name="leave_type"]:checked');
    if (checked) {
        updateUI(checked.value);
    }

    radios.forEach(radio => {
        radio.addEventListener("change", (e) => {
            updateUI(e.target.value);
        });
    });
});
