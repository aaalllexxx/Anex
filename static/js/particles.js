let radius = 120,
    particle = 10,
    offset = 4,
    boxShadow = 20,
    depth = 0.1,
    dir = 1,
    breath_time = 5,
    amplitude = 10,
    decreaser = 0.07,
    shadowCol = "#ffffff",
    onactive = "#48ff6dff";

let scaled = false;
let recording = false;

let circ = document.querySelector("#circ");
circ.style.width = `${radius*2}px`;
circ.style.height = `${radius*2}px`;


for (let y = -radius; y <= radius; y += particle + offset) {
    for (let x = -radius; x <= radius; x += particle + offset) {
        if (x ** 2 + y ** 2 < radius ** 2) {
            let div = document.createElement("div");
            div.classList.add("particle");
            div.style.left = `${x + radius - particle/2}px`;
            div.style.top = `${y + radius - particle/2}px`;
            
            let delta = Math.sqrt(x ** 2 + y ** 2);
            div.style.width = `${particle - delta * decreaser}px`;
            div.style.height = `${particle - delta * decreaser}px`;
            
            let gs = 255 - delta;
            div.style.backgroundColor = `rgb(${gs},${gs},${gs})`;
            div.style.boxShadow = `0 0 ${boxShadow}px #ffffff`;
            
            circ.appendChild(div);
        }
    }
}

let timer = 0;
let level = 0;
let particles = document.querySelectorAll(".particle");
let micStream = null;

async function ensureMicOnce() {
    // Проверить состояние Permissions API
    try {
        const st = await navigator.permissions.query({ name: 'microphone' });
        if (st.state === 'denied') {
            throw new Error('Microphone permission denied');
        }
    } catch (_) {
        // Permissions API может быть не поддержан
    }
    
    // Переиспользовать уже созданный поток
    if (micStream && micStream.getAudioTracks().some(t => t.readyState === 'live')) {
        return micStream;
    }
    
    // Первый и единственный запрос за сессию окна
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    return micStream;
}

async function start() {
    const stream = await ensureMicOnce();
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    
    // ВЧ-фильтр для удаления DC/дрейфа
    const hp = audioContext.createBiquadFilter();
    hp.type = "highpass";
    hp.frequency.value = 30;
    
    // Подключение ворклета
    try {
        await audioContext.audioWorklet.addModule('level-processor.js');
    } catch (e) {
        // Fallback через Blob
        const res = await fetch('/static/js/level-processor.js', { cache: 'no-cache' });
        const code = await res.text();
        const blob = new Blob([code], { type: 'text/javascript' });
        const blobUrl = URL.createObjectURL(blob);
        await audioContext.audioWorklet.addModule(blobUrl);
        URL.revokeObjectURL(blobUrl);
    }
    
    const levelNode = new AudioWorkletNode(audioContext, 'level-processor');
    
    // Соединение: mic -> HP -> worklet (НЕ подключаем к destination)
    source.connect(hp).connect(levelNode);
    
    // Получаем скаляр уровня
    levelNode.port.onmessage = (ev) => {
        const v = ev?.data?.level;
        if (typeof v === 'number' && Number.isFinite(v)) {
            level = v;
            
            // Обновляем частицы при получении нового уровня
            let localdir = 1;
            if (recording) {
                for (let particle of particles) {
                    particle.style.transform = `translateY(${Math.sin(timer) + localdir * level * 3}px) rotate(${timer * .05}rad)`;
                    localdir = -localdir;
                }
            }
            
        }
    };
}

// Вызов старта
start().catch(console.error);

// Анимация свечения
setInterval(() => {
    if (boxShadow >= 25 || boxShadow <= 10) {
        dir = -dir;
    }
    
    boxShadow += dir;
    depth += 0.00001 * dir;
    
    for (let part of document.querySelectorAll(".particle")) {
        if (boxShadow <= 25 || boxShadow >= 10) {
            part.style.boxShadow = `0 0 ${boxShadow}px ${shadowCol}`;
        }
    }
}, 170);

// Основная анимация контейнера
setInterval(() => {
    if (!scaled) {
        circ.style.transform = `translateY(${amplitude * Math.sin(timer)}px) rotate(${timer*.05}rad)`;
    } else {
        circ.style.transform = `translateY(${amplitude * Math.sin(timer)}px) rotate(${timer*.05}rad) scale(1.05)`;
        circ.style.cursor = "pointer"
    }
    timer += .2;
}, 100);

// Функция печатающего текста
function type(text, element, speed) {
    console.log(text);
    element.innerText = "";
    let index = 0;
    const intervalId = setInterval(() => {
        if (text.length > index) {
            element.innerHTML += text[index];
            index += 1;
        } else {
            clearInterval(intervalId); // ИСПРАВЛЕНИЕ: очищаем интервал
        }
    }, speed);
}

let label = document.querySelector(".label");
if (label) {
    type("Задайте вопрос...", label, 90);
}

circ.onmouseover = () => {
    scaled = true;
}

circ.onmouseleave = () => {
    scaled = false;
}

circ.onclick = () => {
    recording = !recording
    let particles = document.querySelectorAll(".particle");
    if (recording) {
        for (let particle of particles) {
            particle.style.backgroundColor = `${onactive}`
        }
    } else {
        let particles = document.querySelectorAll(".particle");
        for (let part of particles) {
            let delta = Math.sqrt((Number.parseInt(part.style.left) + particle/2 - radius) ** 2 + (Number.parseInt(part.style.top) + particle/2 - radius) ** 2);
            let gs = 255 - delta;
            part.style.backgroundColor = `rgb(${gs},${gs},${gs})`;
        }
    }
    shadowCol = recording ? onactive : "#ffffff";
}
