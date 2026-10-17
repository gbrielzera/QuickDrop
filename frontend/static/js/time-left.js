// Calcula quanto tempo falta para a sala expirar.

const MILLISECONDS_PER_MINUTE = 60 * 1000;
const MINUTES_PER_HOUR = 60;

/** Divide uma duração em horas e minutos inteiros. Durações negativas contam como zero. */
export function splitTimeLeft(milliseconds) {
  const totalMinutes = Math.floor(Math.max(milliseconds, 0) / MILLISECONDS_PER_MINUTE);
  return {
    hours: Math.floor(totalMinutes / MINUTES_PER_HOUR),
    minutes: totalMinutes % MINUTES_PER_HOUR,
  };
}
