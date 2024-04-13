// let task = document.querySelectorAll(".task");
let sidebar_elements = document.querySelectorAll(".e");
// let special = document.querySelectorAll(".special");
// task.forEach(element => {
//     let children = element.children;
//     for (let i = 0; i < children.length; i++) {
//         children[i].style.display = "flex";
//         children[i].style.justifyContent = "center";
//         children[i].style.alignItems = "center";
//     }
// });

let prev = null;
sidebar_elements.forEach((element, index) => {
    element.addEventListener("click", () => {
        if (prev !== null) {
            if (!sidebar_elements[prev].classList.contains("special")) {
                sidebar_elements[prev].classList.remove("feature-active");
            }
            else {
                sidebar_elements[prev].classList.remove("special-active");
            }
        }
        if (element.classList.contains("special")) {
            element.classList.add("special-active");
        }
        else {
            element.classList.add("feature-active");
        }
        prev = index;
    });
});
