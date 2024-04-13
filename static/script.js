// let task = document.querySelectorAll(".task");
// let sidebar_elements_text = document.querySelectorAll(".e");
// let sidebar_elements = document.querySelectorAll(".e1");
// let special = document.querySelectorAll(".special");
// let add_button = document.querySelector(".add-button");
// sidebar_elements.forEach(element => {
//     element.style.display = "none";
// })
// task.forEach(element => {
//     let children = element.children;
//     for (let i = 0; i < children.length; i++) {
//         children[i].style.display = "flex";
//         children[i].style.justifyContent = "center";
//         children[i].style.alignItems = "center";
//     }
// });

let prev = null;
// sidebar_elements_text.forEach((element, index) => {
//     element.addEventListener("click", () => {
//         if (prev !== null) {
//             if (!sidebar_elements_text[prev].classList.contains("special")) {
//                 sidebar_elements_text[prev].classList.remove("feature-active");
//             }
//             else {
//                 sidebar_elements_text[prev].classList.remove("special-active");
//             }
//             sidebar_elements[prev].style.display = "none";
//         }
//         if (element.classList.contains("special")) {
//             element.classList.add("special-active");
//         }
//         else {
//             element.classList.add("feature-active");
//         }
//         sidebar_elements[index].style.display = "block";
//         prev = index;
//     });
// });

function active(element) {
    if (prev !== null) {
        if (!sidebar_elements_text[prev].classList.contains("special")) {
            sidebar_elements_text[prev].classList.remove("feature-active");
        }
        else {
            sidebar_elements_text[prev].classList.remove("special-active");
        }
        sidebar_elements[prev].style.display = "none";
    }
    if (element.classList.contains("special")) {
        element.classList.add("special-active");
    }
    else {
        element.classList.add("feature-active");
    }
    sidebar_elements[index].style.display = "block";
    prev = element;
}