document.addEventListener("DOMContentLoaded", function () {
    const workDateInput = document.querySelector("#id_work_date");
    const daysInput = document.querySelector("#id_days");
    const radios = document.querySelectorAll('input[name="leave_type"]');
    const boxW = document.querySelector(".box_w");
    const boxWS = document.querySelector(".box_ws");
    const status = document.querySelector("#request-form-status");

    if (!radios.length || !boxW || !boxWS) return;

    const setSectionVisible = (section, visible, displayClass) => {
        section.classList.toggle("hidden", !visible);
        section.classList.toggle("hide", !visible);
        if (displayClass) {
            section.classList.toggle(displayClass, visible);
        }
        section.hidden = !visible;
        section.style.display = visible ? "" : "none";
        section.querySelectorAll("input, select, textarea").forEach((input) => {
            input.disabled = !visible;
        });
    };

    const updateUI = (value) => {
        const isHoliday = value === "W";
        const requiresWorkDate = value === "WS" || value === "WN";

        setSectionVisible(boxW, isHoliday, "grid");
        setSectionVisible(boxWS, requiresWorkDate);

        if (daysInput) {
            daysInput.disabled = !isHoliday;
            if (!isHoliday) {
                daysInput.removeAttribute("required");
            }
        }

        if (workDateInput) {
            workDateInput.disabled = !requiresWorkDate;
        }

        if (isHoliday && workDateInput) {
            workDateInput.value = "";
        }

        if (status) {
            status.textContent = isHoliday
                ? "Wyświetlono pola wymiaru urlopu i urlopu na żądanie."
                : requiresWorkDate
                    ? "Wyświetlono pole daty pracy."
                    : "Ukryto pola zależne od rodzaju wolnego.";
        }
    };

    const checked = document.querySelector('input[name="leave_type"]:checked');
    if (checked) {
        updateUI(checked.value);
    } else {
        updateUI("");
    }

    radios.forEach((radio) => {
        radio.addEventListener("change", (e) => {
            updateUI(e.target.value);
        });
    });
});
