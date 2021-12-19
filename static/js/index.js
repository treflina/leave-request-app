document.addEventListener("DOMContentLoaded", function () {
  const w = document.querySelector("#id_type_0");
  const ws = document.querySelector("#id_type_1");
  const wn = document.querySelector("#id_type_2");
  const dw = document.querySelector("#id_type_3");
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

//Datepicker - NOT USED
$(function () {
  $(".input-daterange").datepicker({
    format: "dd/mm/yy",
    weekStart: 1,
    language: "pl",
    orientation: "top auto",
    daysOfWeekDisabled: "0,6",
    todayHighlight: true,
  });
});

$(".datepicker").datepicker({
  format: "dd/mm/yy",
  weekStart: 1,
  language: "pl",
  orientation: "top auto",
  daysOfWeekDisabled: "1,2,3,4,5",
  todayHighlight: true,
});

//Numbering automatically rows in tables
function addRowCount(tableAttr) {
  $(tableAttr).each(function () {
    $("th:first-child, thead td:first-child", this).each(function () {
      var tag = $(this).prop("tagName");
      $(this).before("<" + tag + ">Lp.</" + tag + ">");
    });
    $("td:first-child", this).each(function (i) {
      $(this).before("<td>" + (i + 1) + ".</td>");
    });
  });
}
addRowCount(".js-serial");

//Tables search
$(document).ready(function () {
  $("#myInput1").on("keyup", function () {
    var value = $(this).val().toLowerCase();
    $("#myTable1 tr").filter(function () {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
    });
    $("#myTable3 tr td").filter(function () {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
    });
  });
});

function search() {
  const input = document.getElementById("myInput");
  const filter = input.value.toUpperCase();
  const table = document.querySelector(".myTable");
  const tr = table.getElementsByTagName("tr");
  let td, txtValue;

  for (let i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[2];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}

function search2() {
  const input = document.getElementById("myInput2");
  const filter = input.value.toUpperCase();
  const table = document.querySelector(".myTable2");
  const tr = table.getElementsByTagName("tr");
  let td, txtValue;

  for (let i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[2];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}

// inspired by http://jsfiddle.net/arunpjohny/564Lxosz/1/
