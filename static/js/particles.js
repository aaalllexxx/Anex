// Параметры визуализации
let radius = 120,
    particle = 10,
    offset = 5,
    boxShadow = 20,
    depth = 0.1,
    dir = 1,
    breath_time = 5,
    amplitude = 10,
    decreaser = 0.07,
    shadowCol = "#ffffff",
    onactive = "#48ff6dff";

// Состояния
let scaled = false;
let recording = false;
let circPolling = false;
let lastTextTs = 0;
const NO_TEXT_TIMEOUT_MS = 3000; // 3 секунды без текста — выключаем
const POLL_INTERVAL_MS = 120;    // частота опроса эндпоинта
const FETCH_TIMEOUT_MS = 2500;   // таймаут одного запроса

// DOM
let mic = document.querySelector(".mic");
let mic_img = document.querySelector(".mic_img");
let circ = document.querySelector("#circ");
let circ_out = document.querySelector(".circ_outer");
let label = document.querySelector(".label");
if (!label) {
  label = document.createElement("h1");
  label.className = "label";
  document.body.prepend(label);
}

// Геометрия круга/частиц
circ.style.width = `${radius*2}px`;
circ.style.height = `${radius*2}px`;
if (mic) mic.style.transform = `translate(${particle/2}px, ${particle/2}px)`;

for (let y = -radius; y <= radius; y += particle + offset) {
  for (let x = -radius; x <= radius; x += particle + offset) {
    if (x ** 2 + y ** 2 < radius ** 2) {
      let div = document.createElement("div");
      div.classList.add("particle");
      div.style.left = `${x + radius}px`;
      div.style.top = `${y + radius}px`;

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

// Печатная машинка: состояние
let tw_target = "";   // последняя целевая строка с сервера
let tw_shown = "";    // уже отображённое
let tw_timer = null;
const TYPE_SPEED_MS = 90;

// Инициализация подсказки при загрузке
typewriter_set("Задайте вопрос...");

// Поллинг эндпоинта /get_speech
let pollTimerId = null;
let backoffFails = 0;

async function fetchWithTimeout(url, init = {}, timeoutMs = FETCH_TIMEOUT_MS) {
  let useNativeTimeout = typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function";
  if (useNativeTimeout) {
    const res = await fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) });
    return res;
  } else {
    const controller = new AbortController();
    const tId = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...init, signal: controller.signal });
      return res;
    } finally {
      clearTimeout(tId);
    }
  }
}

async function pollOnce() {
  try {
    const res = await fetchWithTimeout("/get_speech", { method: "GET", headers: { "accept": "application/json" } }, FETCH_TIMEOUT_MS);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const { text, rms, dbfs } = data ?? {};

    // Уровень для анимации
    if (Number.isFinite(rms)) {
      level = Math.max(0, Math.min(1, rms / 8000)) * 100;
    } else {
      level = 0;
    }

    // Обновление цели печатной машинки: только рост, без отката
    if (typeof text === "string") {
      const incoming = text.trim();
      // если пришло больше, чем уже показано — допечатываем
      if (incoming.length > tw_shown.length) {
        tw_target = incoming;
        if (!tw_timer) typewriter_tick(); // гарантируем запуск печати
        lastTextTs = performance.now();
        if (!recording) activateUIColors();
        recording = true;
      } else if (incoming.length > 0) {
        // пришёл такой же размер — просто обновим метку активности
        lastTextTs = performance.now();
        if (!recording) activateUIColors();
        recording = true;
      }
    }

    // Анимация частиц от уровня
    animateParticlesFromLevel(level);

    backoffFails = 0;
  } catch (e) {
    backoffFails += 1;
  } finally {
    const since = performance.now() - lastTextTs;
    if (recording && since >= NO_TEXT_TIMEOUT_MS) {
      // Завершение записи: отключаем прослушивание и сбрасываем UI к заглушке
      finishRecordingAndReset();
      return;
    }
  }
}

function startPolling() {
  if (circPolling) return;
  resetSession();           // начинаем «с нуля»
  circPolling = true;
  recording = true;
  lastTextTs = performance.now();
  activateUIColors();
  pollTimerId = setInterval(pollOnce, POLL_INTERVAL_MS);
}

function stopPolling() {
  circPolling = false;
  recording = false;
  if (pollTimerId) {
    clearInterval(pollTimerId);
    pollTimerId = null;
  }
}

function stopPollingWithMicOffAnimation() {
  stopPolling();
  deactivateUIColors();
  level = 0;
  for (let particle of particles) {
    particle.style.transform = `translateY(${Math.sin(timer)}px) rotate(${timer * .05}rad)`;
  }
}

// Полный сценарий завершения записи с возвратом заглушки
function finishRecordingAndReset() {
  stopPollingWithMicOffAnimation();
  resetTypewriter("Задайте вопрос...");
}

// Сброс печатной машинки к заглушке
function resetTypewriter(placeholder) {
  if (tw_timer) {
    clearTimeout(tw_timer);
    tw_timer = null;
  }
  tw_target = String(placeholder ?? "");
  tw_shown = "";
  label.innerText = "";
  typewriter_tick();
}

// Сброс сессии перед новым запуском записи
function resetSession() {
  // Сбрасываем печатную машинку и уровень
  if (tw_timer) {
    clearTimeout(tw_timer);
    tw_timer = null;
  }
  tw_target = "";
  tw_shown = "";
  label.innerText = "";
  level = 0;
  lastTextTs = 0;
  // Возвращаем начальную подсказку немедленно
  typewriter_set("Задайте вопрос...");
}

// Визуальные состояния
function activateUIColors() {
  shadowCol = onactive;
  if (mic_img) mic_img.src = "/static/imgs/micon.png";
  for (let particle of particles) {
    particle.style.backgroundColor = `${onactive}`;
  }
}

setInterval(
  () => {
    for (let part of document.querySelectorAll(".particle")) {
      let delta = Math.sqrt((Number.parseInt(part.style.left) - radius) ** 2 + (Number.parseInt(part.style.top) - radius) ** 2);
      part.style.transform = `scale(${0.6 + Math.sin(particle - delta * decreaser)/3})`;
    }
    decreaser += .005
    console.log(decreaser)
  },
  200
)

function deactivateUIColors() {
  shadowCol = "#ffffff";
  if (mic_img) mic_img.src = "/static/imgs/micoff.png";
  for (let part of particles) {
    let delta = Math.sqrt((Number.parseInt(part.style.left) - radius) ** 2 + (Number.parseInt(part.style.top) - radius) ** 2);
    let gs = 255 - delta;
    part.style.backgroundColor = `rgb(${gs},${gs},${gs})`;
  }
}

// Анимация свечения (дыхание)
setInterval(() => {
  if (boxShadow >= 25 || boxShadow <= 10) dir = -dir;
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
  circ.style.transform = `rotate(${timer*.05}rad)`;
  if (!scaled) {
    circ_out.style.transform = `translateY(${amplitude * Math.sin(timer)}px)`;
  } else {
    circ_out.style.cursor = "pointer";
    circ_out.style.transform = `translateY(${amplitude * Math.sin(timer)}px) scale(1.05)`;
  }
  timer += .2;
}, 100);

// Перерисовка частиц от уровня
function animateParticlesFromLevel(lvl) {
  let localdir = 1;
  let dy = 0;
  for (let particle of particles) {
    dy = Math.sin(timer) + localdir * (lvl + (Math.random() - 0.5) * 2) * 6;
    particle.style.transform = `translateY(${dy}px) rotate(${timer * .05}rad)`;
    localdir = -localdir;
  }
}

// Печатная машинка: API
function typewriter_set(text) {
  // Полная установка цели (используется для показа заглушки)
  tw_target = String(text ?? "");
  tw_shown = "";
  label.innerText = "";
  if (tw_timer) {
    clearTimeout(tw_timer);
    tw_timer = null;
  }
  typewriter_tick();
}

function typewriter_tick() {
  if (tw_shown.length < tw_target.length) {
    tw_shown = tw_target.slice(0, tw_shown.length + 1);
    label.innerText = tw_shown;
    tw_timer = setTimeout(typewriter_tick, TYPE_SPEED_MS);
    return;
  }
  if (tw_timer) {
    clearTimeout(tw_timer);
    tw_timer = null;
  }
}

// Ховеры круга
circ_out.onmouseover = () => { scaled = true; };
circ_out.onmouseleave = () => { scaled = false; };

// Клик по кругу: старт/стоп опроса эндпоинта
circ_out.onclick = () => {
  if (!circPolling) {
    startPolling();          // старт новой сессии: заглушка показана, затем поступают partial’ы
  } else {
    finishRecordingAndReset(); // явное завершение: остановиться и вернуть заглушку
  }
};
