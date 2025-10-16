// resizeElement.js
/**
 * Добавляет возможность изменения размеров указанного элемента
 * @param {HTMLElement} element — элемент, размеры которого можно изменять
 * @param {'left'|'right'|'top'|'bottom'} side — сторона, с которой можно тянуть
 */
function enableResize(element, side) {
    const handle = document.createElement("div");
    handle.style.position = "absolute";
    handle.style.userSelect = "none";

    const thickness = 6; // ширина / высота области захвата

    switch (side) {
        case "right":
            handle.style.right = "0";
            handle.style.top = "0";
            handle.style.width = thickness + "px";
            handle.style.height = "100%";
            handle.style.cursor = "ew-resize";
            break;
        case "left":
            handle.style.left = "0";
            handle.style.top = "0";
            handle.style.width = thickness + "px";
            handle.style.height = "100%";
            handle.style.cursor = "ew-resize";
            break;
        case "bottom":
            handle.style.bottom = "0";
            handle.style.left = "0";
            handle.style.width = "100%";
            handle.style.height = thickness + "px";
            handle.style.cursor = "ns-resize";
            break;
        case "top":
            handle.style.top = "0";
            handle.style.left = "0";
            handle.style.width = "100%";
            handle.style.height = thickness + "px";
            handle.style.cursor = "ns-resize";
            break;
        default:
            throw new Error("Недопустимое значение стороны");
    }

    element.style.position = element.style.position || "relative";
    element.appendChild(handle);

    let startX, startY, startWidth, startHeight;

    handle.addEventListener("mousedown", function (e) {
        e.preventDefault();
        startX = e.clientX;
        startY = e.clientY;
        startWidth = parseInt(window.getComputedStyle(element).width, 10);
        startHeight = parseInt(window.getComputedStyle(element).height, 10);

        function onMouseMove(e) {
            if (side === "right") {
                const newWidth = startWidth + (e.clientX - startX);
                console.log(e.clientX - startX)
                element.style.width = Math.max(newWidth, 20) + "px";
            } else if (side === "left") {
                const newWidth = startWidth - (e.clientX - startX);
                element.style.width = Math.max(newWidth, 20) + "px";
                element.style.left = element.offsetLeft + (e.clientX - startX) + "px";
            } else if (side === "bottom") {
                const newHeight = startHeight + (e.clientY - startY);
                element.style.height = Math.max(newHeight, 20) + "px";
            } else if (side === "top") {
                const newHeight = startHeight - (e.clientY - startY);
                element.style.height = Math.max(newHeight, 20) + "px";
                element.style.top = element.offsetTop + (e.clientY - startY) + "px";
            }
        }

        function onMouseUp() {
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
        }

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    });
}

let chats = document.querySelector(".chats")

enableResize(chats, "right");