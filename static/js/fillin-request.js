document.addEventListener("DOMContentLoaded", function () {
    const w = document.querySelector("#id_leave_type_0");
    const ws = document.querySelector("#id_leave_type_1");
    const wn = document.querySelector("#id_leave_type_2");
    const dw = document.querySelector("#id_leave_type_3");
    const box_w = document.querySelector(".box_w");
    const box_ws = document.querySelector(".box_ws");

    const hide_ws = function () {
        box_w.classList.add("hide");
        box_ws.classList.remove("hide");
    };

    const hide_w = function () {
        box_ws.classList.add("hide");
        box_w.classList.remove("hide");
    };

    const hide_all = () => {
        box_ws.classList.add("hide");
        box_w.classList.add("hide");
    };
    if (ws.checked == true || wn.checked == true) {
        box_w.classList.add("hide");
        box_ws.classList.remove("hide");
    } else if (w.checked == true) {
        box_ws.classList.add("hide");
        box_w.classList.remove("hide");
    } else if (dw.checked == true) {
        box_ws.classList.add("hide");
        box_w.classList.add("hide");
    }

    w.addEventListener("change", hide_w);
    ws.addEventListener("change", hide_ws);
    wn.addEventListener("change", hide_ws);
    dw.addEventListener("change", hide_all);
});
