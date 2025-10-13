// level-processor.js — расчёт уровня RMS + огибающая attack/release.
// Ничего не выводит в колонки, только шлёт {level} в главный поток.

class LevelProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._env = 0;       // огибающая
    this._attack = 0.5;  // быстрый подъём
    this._release = 0.05;// медленный спад
    this._scale = 200;   // масштаб для пикселей
    this._maxPx = 1000;  // ограничение уровня
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;

    const ch = input[0]; // первый канал
    let sumSq = 0;
    for (let i = 0; i < ch.length; i++) {
      const s = ch[i];
      sumSq += s * s;
    }

    const rms = Math.sqrt(sumSq / (ch.length || 1)); // 0..1
    const target = rms;
    const coeff = target > this._env ? this._attack : this._release;
    this._env = this._env + coeff * (target - this._env);

    const levelPx = Math.min(this._env * this._scale, this._maxPx);
    this.port.postMessage({ level: levelPx });

    return true;
  }
}

registerProcessor('level-processor', LevelProcessor);
