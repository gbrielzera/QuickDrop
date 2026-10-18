// Conexão em tempo real com a sala (WebSocket), que se reconecta sozinha.
//
// No celular a conexão cai com frequência (a tela apaga, o Wi-Fi oscila), então reconectar
// sem a pessoa perceber é parte essencial do app.

// Um "ping" de tempos em tempos evita que roteadores e proxies derrubem uma conexão parada.
const PING_INTERVAL_MILLISECONDS = 25 * 1000;

const FIRST_RECONNECT_DELAY_MILLISECONDS = 1000;
const MAX_RECONNECT_DELAY_MILLISECONDS = 30 * 1000;

/** Quanto esperar antes da tentativa número `attempt` (0, 1, 2...): 1s, 2s, 4s... até 30s. */
export function reconnectDelay(attempt) {
  return Math.min(FIRST_RECONNECT_DELAY_MILLISECONDS * 2 ** attempt, MAX_RECONNECT_DELAY_MILLISECONDS);
}

function roomSocketUrl(roomCode) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${location.host}/ws/rooms/${roomCode}`;
}

/**
 * Abre a conexão da sala e a mantém aberta.
 * - onMessage: recebe cada mensagem do servidor (já convertida de JSON).
 * - onOpen: chamada a cada vez que a conexão abre (a primeira e depois de cada reconexão).
 * - onClose: chamada a cada vez que a conexão cai.
 * - shouldReconnect: função assíncrona; devolve false se não vale mais a pena tentar (ex.: a sala expirou).
 */
export function connectRoomSocket({ roomCode, onMessage, onOpen, onClose, shouldReconnect }) {
  let failedAttempts = 0;
  let pingTimer = null;

  function open() {
    const socket = new WebSocket(roomSocketUrl(roomCode));

    socket.addEventListener("open", () => {
      failedAttempts = 0;
      pingTimer = setInterval(() => socket.send(JSON.stringify({ type: "ping" })), PING_INTERVAL_MILLISECONDS);
      onOpen();
    });

    socket.addEventListener("message", (event) => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch {
        return; // mensagem que não é JSON: ignora
      }
      onMessage(message);
    });

    socket.addEventListener("close", async () => {
      clearInterval(pingTimer);
      onClose();
      if (!(await shouldReconnect())) {
        return;
      }
      setTimeout(open, reconnectDelay(failedAttempts));
      failedAttempts++;
    });
  }

  open();
}
