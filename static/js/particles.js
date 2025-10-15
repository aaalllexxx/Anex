// Параметры визуализации
let radius = 120,
    particle = 10,
    offset = 2,
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
if (mic) mic.style.transform = `translateY(${particle/2}px)`;

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

// Текст при запуске
type("Задайте вопрос...", label, 90);

// Поллинг эндпоинта /get_speech
let pollTimerId = null;
let backoffFails = 0; // можно использовать для бэкоффа при ошибках сети

async function fetchWithTimeout(url, init = {}, timeoutMs = FETCH_TIMEOUT_MS) {
  // Используем AbortSignal.timeout, где поддерживается
  // В большинстве современных браузеров доступно; при отсутствии — fallback
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
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    // Ожидаем {"text": string, "rms": number, "dbfs": number}
    const { text, rms, dbfs } = data ?? {};
    // Уровень для анимации
    if (Number.isFinite(rms)) {
      // Простейшая нормализация: rms (0..32768) -> уровень смещения
      level = Math.max(0, Math.min(1, rms / 8000)); // подстройте масштаб под ваши данные
    } else {
      level = 0;
    }

    // Обновление текста
    if (typeof text === "string" && text.trim().length > 0) {
      label.innerText = text;
      lastTextTs = performance.now();
      // Активная подсветка при наличии текста
      if (!recording) {
        // если пришёл текст, но UI не в режиме записи — подсветим
        activateUIColors();
      }
      recording = true;
    }

    // Анимация частиц от уровня
    animateParticlesFromLevel(level);

    backoffFails = 0; // сброс неудач при успешном запросе
  } catch (e) {
    // Ошибки сети/таймаут — мягкая обработка, можно добавить бэкофф
    backoffFails += 1;
  } finally {
    // Проверка таймаута "нет текста 3 секунды"
    const since = performance.now() - lastTextTs;
    if (recording && since >= NO_TEXT_TIMEOUT_MS) {
      stopPollingWithMicOffAnimation();
      return;
    }
  }
}

function startPolling() {
  if (circPolling) return;
  circPolling = true;
  recording = true;
  lastTextTs = performance.now();
  activateUIColors();
  // Частый опрос + requestAnimationFrame-анимация ниже
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
  // Вернуть частицы к пассивной палитре и иконку микрофона
  deactivateUIColors();
  // Плавно «успокоить» частицы (сброс level)
  level = 0;
}

// Визуальные состояния
function activateUIColors() {
  shadowCol = onactive;
  if (mic_img) mic_img.src = "/static/imgs/micon.png";
  for (let particle of particles) {
    particle.style.backgroundColor = `${onactive}`;
  }
}

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
  // lvl в диапазоне ~0..1; используем синус и чередуем направление
  let localdir = 1;
  const dy = Math.sin(timer) + localdir * lvl * 6; // чувствительность
  for (let particle of particles) {
    particle.style.transform = `translateY(${dy}px) rotate(${timer * .05}rad)`;
    localdir = -localdir;
  }
}

// Подсказочный текст печатной машинкой
function type(text, element, speed) {
  element.innerText = "";
  let index = 0;
  const intervalId = setInterval(() => {
    if (text.length > index) {
      element.innerHTML += text[index];
      index += 1;
    } else {
      clearInterval(intervalId);
    }
  }, speed);
}

// Ховеры круга
circ_out.onmouseover = () => {
  scaled = true;
};
circ_out.onmouseleave = () => {
  scaled = false;
};

// Клик по кругу: старт/стоп опроса эндпоинта
circ_out.onclick = () => {
  if (!circPolling) {
    startPolling();
  } else {
    stopPollingWithMicOffAnimation();
  }
};
