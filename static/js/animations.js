let container = document.querySelector('#index_c1');
let arrow = document.querySelector('.slide_to_chat');

let slided = false;

arrow.onmouseenter = () => {
    container.style.transform = 'translateY(-20px)';
    container.style.cursor  = 'pointer';
}

arrow.onmouseleave = () => {
    if (!slided) {
        container.style.transform = 'translateY(0px)';
        container.style.cursor  = 'default';
    }
}
arrow.onclick = () => {
    container.style.transform = `translateY(-100%)`;
    container.style.cursor  = 'default';
    slided = true;
}

let chats = document.querySelectorAll('.chat');

for (let chat of chats) {
    chat.onmouseenter = () => {
        if (!chat.classList.contains('active_chat'))
            chat.style.backgroundColor = 'rgba(214, 214, 214, 1)';
        chat.style.cursor = 'pointer';
    }
    chat.onmouseleave = () => {
        if (!chat.classList.contains('active_chat'))
            chat.style.removeProperty('background-color');
        chat.style.cursor = 'default';
    }
    chat.onclick = () => {
        chat.style.removeProperty('background-color');
        for (let chat of chats) {
            if (chat.classList.contains('active_chat')) {
                chat.classList.remove('active_chat');
            }
        }
        chat.classList.add('active_chat');
        
    }
}