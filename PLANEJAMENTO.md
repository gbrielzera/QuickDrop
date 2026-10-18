# Planejamento — Transferidor de Arquivos e Textos em Tempo Real

> Nome provisório: **QuickDrop**. Uma aplicação web onde você cria uma *sala* (sessão) com **código + senha**, entra nela de vários dispositivos e envia/baixa arquivos e textos, com tudo aparecendo na hora nos outros aparelhos.

---

## 1. Visão geral

### Problema
Mandar um arquivo ou um trecho de texto do PC para o celular (ou para outro PC) costuma exigir e-mail, WhatsApp ou sites de upload lentos e cheios de anúncios.

### Solução
1. No dispositivo A você cria uma sala e recebe um **código** (ex.: `K7P-3XM`) e define uma **senha**.
2. No dispositivo B você digita o código e a senha (ou lê um **QR Code**).
3. Os dois dispositivos passam a ver a mesma área de **arquivos** e o mesmo **editor de texto**, que se atualizam **em tempo real**.
4. A sala **expira sozinha** depois de um tempo (padrão 12h, máximo 48h), e tudo é apagado.

### Funcionalidades do MVP (primeira versão utilizável)
- Criar sala com código gerado, **senha opcional** e tempo de expiração (**1h, 12h, 24h ou 48h**; padrão **12h**).
- Entrar na sala com o código (e a senha, se houver), ou pelo **link/QR Code**.
- **Criptografia de ponta a ponta**: arquivos, nomes de arquivos, texto e clips são criptografados no navegador. O servidor só guarda dados embaralhados (ver seção 6).
- Upload de arquivos (arrastar e soltar, botão, e **colar imagem com Ctrl+V**), com barra de progresso.
- Lista de arquivos com download e exclusão, que se atualiza sozinha nos outros aparelhos.
- **Editor de texto compartilhado** sincronizado em tempo real, **e** **clips** (cartões com textos colados, cada um com botão "copiar").
- Expiração automática e limpeza das salas.
- Funcionar bem no celular (layout responsivo).

### Funcionalidades futuras (depois do MVP)
- Lista de dispositivos conectados ("2 dispositivos online").
- Pré-visualização de imagens, PDFs e vídeos (feita no navegador, depois de descriptografar).
- Baixar todos os arquivos em um `.zip` (montado no navegador).
- Upload de arquivos grandes em partes (retomável).
- Transferência direta P2P (WebRTC) para arquivos muito grandes na mesma rede.
- PWA (instalar no celular como app, "Compartilhar com…" do Android).

### Decisões já tomadas
| # | Tema | Decisão |
|---|---|---|
| 1 | Framework | **FastAPI** |
| 2 | Expiração | Opções **1h / 12h / 24h / 48h**, padrão **12h** |
| 3 | Limites | **100 MB por arquivo**, **500 MB por sala** |
| 4 | Senha | **Opcional**, quem cria a sala decide |
| 5 | Texto | **Editor compartilhado + clips** |
| 6 | Front-end | **Jinja2 + JavaScript puro** |
| 7 | Hospedagem | **Rede local primeiro**, internet depois (o projeto já nasce preparado para as duas) |
| 8 | Criptografia de ponta a ponta | **Desde o início** |
| 9 | Tipos de arquivo | **Todos permitidos** (PDF, DOCX, XML, TXT, extensões raras…); só há limite de tamanho |
| 10 | Organização | **`backend/` e `frontend/` em pastas separadas** (o backend serve o frontend) |
| 11 | Código | **Clean code sempre**: simples o bastante para um iniciante entender (regras em `CLAUDE.md`) |

---

## 2. Escolha do framework: **FastAPI** (recomendado)

| Critério | FastAPI | Flask | Django |
|---|---|---|---|
| WebSocket (tempo real) | **Nativo** | Precisa de extensão (flask-sock / Flask-SocketIO) | Precisa do Django Channels (mais complexo) |
| Assíncrono (muitas conexões abertas ao mesmo tempo) | **Nativo (asyncio)** | Limitado | Parcial |
| Upload/download de arquivos em streaming | Fácil | Fácil | Fácil |
| Curva de aprendizado | Baixa/média | Baixa | Média/alta |
| "Coisas prontas" (admin, auth, ORM) | Você escolhe as peças | Você escolhe as peças | Tudo incluso (muita coisa que você não vai usar) |
| Documentação automática da API | **Sim (`/docs`)** | Não | Não |

**Por que FastAPI:** o coração desse projeto é *tempo real*, ou seja, manter várias conexões WebSocket abertas e avisar todos os dispositivos quando algo muda. O FastAPI faz isso nativamente e de forma assíncrona, sem extensões. O Django seria pesado demais para um app tão focado, e o Flask exigiria remendos para o WebSocket.

---

## 3. Onde guardar os dados (a grande dúvida)

### Por que **não** usar o localStorage como armazenamento principal
O `localStorage` fica **dentro do navegador de cada dispositivo**. O celular não consegue ler o localStorage do PC; ele não serve para *transferir* nada. Além disso, tem limite de ~5 MB e não guarda arquivos binários direito.

**Uso correto do localStorage aqui:** só conveniências locais, como lembrar a última sala acessada, o tema (claro/escuro) ou um apelido do dispositivo.

### Arquitetura de armazenamento recomendada

| O quê | Onde | Por quê |
|---|---|---|
| **Metadados** (salas, hash da senha, lista de arquivos, texto do editor) | **SQLite** (no início) → **PostgreSQL** (em produção, se precisar) | SQLite é um arquivo só, sem servidor para instalar, perfeito para começar. Com SQLAlchemy/SQLModel a troca para PostgreSQL depois é quase só mudar a URL de conexão. |
| **Arquivos enviados** | **Sistema de arquivos do servidor** (pasta `storage/`) → opcionalmente **S3 / Cloudflare R2** depois | Banco de dados não é lugar de arquivo grande. No disco é rápido e simples. Cada arquivo é salvo com um nome UUID, nunca com o nome original. |
| **Conexões em tempo real** (quem está online em cada sala) | **Memória do processo Python** → **Redis** (só se rodar mais de um servidor) | Para um servidor só, um dicionário em memória basta. Redis Pub/Sub só é necessário se você escalar para várias instâncias. |
| **Preferências locais** | **localStorage** | Última sala, tema, apelido do dispositivo. |

### Alternativa considerada: P2P puro (WebRTC), sem servidor guardando nada
- ✅ Privacidade máxima, sem custo de armazenamento.
- ❌ Os **dois dispositivos precisam estar online ao mesmo tempo**; não dá para "subir no PC agora e baixar no celular depois". Também é bem mais complexo (sinalização, NAT, servidores TURN).
- **Conclusão:** fica como funcionalidade futura opcional, não como base.

---

## 4. Arquitetura

```
┌────────────────┐        HTTPS (REST)         ┌─────────────────────────────┐
│  Navegador PC  │ ─── upload/download/login ─▶│                             │
│                │◀══════ WebSocket ══════════▶│        FastAPI (Uvicorn)    │
└────────────────┘    eventos em tempo real    │                             │
                                               │  ┌───────────────────────┐  │
┌────────────────┐                             │  │ ConnectionManager     │  │
│ Navegador Cel. │ ─── upload/download/login ─▶│  │ (salas → websockets)  │  │
│                │◀══════ WebSocket ══════════▶│  └───────────────────────┘  │
└────────────────┘                             │  ┌───────────────────────┐  │
                                               │  │ Tarefa de limpeza     │  │
                                               │  │ (apaga salas vencidas)│  │
                                               │  └───────────────────────┘  │
                                               └──────┬───────────────┬──────┘
                                                      │               │
                                               ┌──────▼─────┐  ┌──────▼──────┐
                                               │  SQLite    │  │  storage/   │
                                               │ (metadados)│  │ (arquivos)  │
                                               └────────────┘  └─────────────┘
```

**Regra importante de design:**
- **Arquivos trafegam por HTTP normal** (POST multipart para upload, GET para download). HTTP é feito para isso: tem barra de progresso, streaming, cache e retomada.
- **O WebSocket só carrega avisos pequenos** ("arquivo X foi adicionado", "o texto mudou"). Mandar arquivos pelo WebSocket é uma armadilha comum: trava a conexão e complica tudo.

### Fluxo: enviar um arquivo
1. Celular faz `POST /api/rooms/{code}/files` com o arquivo.
2. O servidor salva em disco aos poucos (streaming, sem carregar tudo na RAM) e registra no banco.
3. O servidor manda pelo WebSocket para **todos da sala**: `{"type": "file_added", "file": {...}}`.
4. O PC recebe o evento e adiciona o arquivo na lista instantaneamente.

### Fluxo: editar o texto
1. Usuário digita no PC; após ~600 ms sem digitar (*debounce*), o navegador criptografa e envia `PUT /api/rooms/{code}/text` com `base_version: 12`.
2. O servidor salva, incrementa a versão para 13 e repassa para os outros dispositivos.
3. O celular atualiza o editor (preservando a posição do cursor quando possível).

---

## 5. Sincronização do editor de texto

Esse é o ponto mais delicado do projeto. Há três níveis de sofisticação:

| Abordagem | Como funciona | Prós | Contras | Quando usar |
|---|---|---|---|---|
| **1. Última escrita vence** (com número de versão) | Cada alteração envia o texto inteiro; o servidor guarda o mais recente | Muito simples | Se duas pessoas digitarem **ao mesmo tempo**, uma sobrescreve a outra | **MVP**: seu caso de uso é "colar aqui, ler lá", raramente duas pessoas digitam juntas |
| 2. Diffs/patches | Envia só a diferença (ex.: `diff-match-patch`) | Menos tráfego, mescla melhor | Mais complexo, ainda pode ter conflitos | Se o texto ficar grande |
| **3. CRDT (Yjs)** | Estrutura de dados que mescla edições simultâneas sem conflito (como no Google Docs) | Edição colaborativa de verdade | Biblioteca JS + `pycrdt` no Python; mais peças | **Fase futura**, se quiser colaboração real |

**Recomendação:** começar com a **abordagem 1**, com um detalhe a mais: se chegar uma atualização remota enquanto o usuário está digitando, mostrar um aviso discreto ("texto alterado em outro dispositivo, atualizar?") em vez de sobrescrever na hora. Migrar para Yjs só se sentir necessidade.

**Ideia extra que combina muito com o objetivo:** além do editor único, ter uma lista de **"clips"**: cada texto colado vira um cartão com botão "copiar". Isso resolve 90% dos casos ("quero mandar esse link/senha/trecho para o celular") sem nenhum conflito de edição.

---

## 6. Segurança (código + senha)

| Risco | Medida |
|---|---|
| Senha vazada do banco | Guardar só o **hash** com **Argon2** (`argon2-cffi`). Nunca a senha em texto. |
| Alguém tentando adivinhar código/senha (força bruta) | **Rate limiting** no login: ex. 5 tentativas por minuto por IP e por sala; bloqueio temporário. |
| Código fácil de adivinhar | Código de 6 caracteres gerado com `secrets` (não `random`), alfabeto sem caracteres ambíguos (sem `0/O`, `1/I/L`): ~31⁶ ≈ 887 milhões de combinações. Com senha, ela também é exigida; sem senha, quem só tem o código ainda não consegue ler o conteúdo (ver 6.1). |
| Acesso sem login após entrar | Ao entrar, o servidor emite um **token de sessão** (cookie `HttpOnly`, `Secure`, `SameSite=Strict`, assinado com `itsdangerous` ou JWT) com validade igual à da sala. Toda requisição REST e o WebSocket validam esse token. |
| Path traversal (arquivo chamado `../../etc/passwd`) | Salvar no disco **sempre com UUID**; o nome original fica só no banco e é sanitizado no download (`Content-Disposition`). |
| Encher o disco do servidor | Limites: ex. **100 MB por arquivo**, **500 MB por sala**, número máximo de salas ativas. Validar o tamanho **durante** o streaming, não só no fim. |
| XSS (script malicioso no texto ou no nome do arquivo) | No front, inserir conteúdo com `textContent`, nunca `innerHTML`. Header `Content-Security-Policy`. |
| Arquivo HTML/SVG malicioso aberto no navegador | **Todos os tipos de arquivo são permitidos** (sem lista de extensões). A proteção vem de: servir downloads com `Content-Disposition: attachment` e `X-Content-Type-Options: nosniff`, e nunca renderizar HTML/SVG do usuário na pré-visualização. Como o conteúdo chega criptografado, o servidor nem sabe o tipo real. |
| Interceptação na rede | **HTTPS obrigatório** em produção (o WebSocket vira `wss://`). |
| Dados esquecidos para sempre | Expiração automática + botão "encerrar sala agora" que apaga tudo. |

### 6.1 Criptografia de ponta a ponta (E2E), desde o início

**Princípio:** tudo é criptografado e descriptografado **no navegador**. O servidor recebe e guarda só bytes embaralhados e **nunca** vê a senha, a chave, o conteúdo dos arquivos, os nomes dos arquivos nem o texto. O servidor vê apenas: código da sala, horários, tamanho aproximado dos arquivos e quantos dispositivos estão conectados.

#### Biblioteca: **libsodium.js** (`libsodium-wrappers-sumo`), servida pelo próprio app (sem CDN)
Por que não a Web Crypto API nativa do navegador: o `crypto.subtle` **só funciona em HTTPS ou `localhost`**. Na fase de rede local você vai acessar pelo celular via `http://192.168.x.x:8000`, e lá ele simplesmente **não existe**. A libsodium.js roda em qualquer contexto e ainda oferece primitivas melhores:

| Função | Primitiva libsodium | Para quê |
|---|---|---|
| Derivar chave da senha | `crypto_pwhash` (**Argon2id**) | Transforma a senha em uma chave-mestra de 32 bytes, de forma lenta de propósito (dificulta força bruta) |
| Separar chaves | `crypto_kdf_derive_from_key` | Da chave-mestra saem duas subchaves independentes: `auth_key` e `enc_key` |
| Criptografar arquivos | `crypto_secretstream_xchacha20poly1305` | Criptografa em **blocos de 1 MB**, sem precisar do arquivo inteiro na memória; detecta adulteração e truncamento |
| Criptografar textos, clips e metadados | `crypto_secretbox_easy` (XSalsa20-Poly1305) com nonce aleatório de 24 bytes, guardado junto do texto cifrado | Mensagens pequenas |

#### Como as chaves funcionam

**Sala com senha:**
```
senha + salt da sala ──Argon2id──▶ chave-mestra
                                   ├─ KDF("auth") ─▶ auth_key ──▶ enviada ao servidor para provar que sabe a senha
                                   │                              (o servidor guarda só Argon2(auth_key))
                                   └─ KDF("enc")  ─▶ enc_key  ──▶ NUNCA sai do navegador; criptografa tudo
```
- O servidor confere o `auth_key` para liberar o acesso, mas **não consegue** chegar na `enc_key` a partir dele (a KDF é de mão única).
- O `salt` é gerado aleatoriamente pelo navegador na criação da sala e guardado no servidor (não é segredo).

**Sala sem senha:**
- O navegador gera uma `enc_key` **aleatória de 32 bytes**.
- Essa chave vai no **fragmento do link**: `http://.../r/K7P3XM#k=ab12cd...`. O que vem depois do `#` **nunca é enviado ao servidor** pelo navegador; fica só no dispositivo.
- O jeito de entrar no outro dispositivo é pelo **link ou QR Code** (por isso o QR Code entrou no MVP).
- Quem tiver só o código consegue entrar, mas vê apenas conteúdo ilegível.
- ⚠️ Decisão pendente sobre isso na seção 16.

**No dispositivo:** depois de entrar, a `enc_key` fica guardada no `sessionStorage` da aba (para não pedir a senha a cada F5) e é apagada ao fechar a aba.

#### O que é criptografado
| Item | No servidor fica |
|---|---|
| Conteúdo do arquivo | Arquivo `.bin` criptografado em blocos (secretstream) |
| Nome, tipo MIME e tamanho original | Um campo `encrypted_meta` (JSON criptografado) |
| Texto do editor | `ciphertext` (o nonce vai junto, nos primeiros 24 bytes) |
| Cada clip | `ciphertext` (idem) |
| Apelido do dispositivo | Também criptografado (aparece só para quem tem a chave) |

#### Consequências práticas (bom saber desde já)
- **Esqueceu a senha = dados perdidos.** Ninguém, nem o servidor, consegue recuperar. Como as salas expiram em no máximo 48h, isso é aceitável.
- **Senha fraca continua sendo fraca:** quem roubar o banco pode tentar adivinhar offline. O Argon2id deixa isso lento; o app deve exigir **no mínimo 6 caracteres**.
- **Pré-visualização, `.zip` e busca** passam a ser feitos no navegador, depois de descriptografar.
- **Download:** o navegador baixa o `.bin`, descriptografa bloco a bloco e entrega o arquivo final com `Blob` + link de download. Para 100 MB isso funciona bem em qualquer celular moderno.
- **Sincronização do editor** continua igual (última escrita vence); só que o que trafega é o texto criptografado.
- **Limitação honesta do E2E em aplicação web:** o JavaScript vem do próprio servidor. Se o servidor for comprometido, ele pode entregar um JS malicioso. Isso vale para qualquer app web com E2E. Mitigações: servir a libsodium localmente com **Subresource Integrity**, CSP rígida e, mais tarde, HTTPS obrigatório.

---

## 7. Modelo de dados

```text
Room (sala)
├── id               UUID (PK)
├── code             str(6), único, indexado   ex.: "K7P3XM"
├── has_password     bool                      true = o criador escolheu a senha; false = o app gerou um segredo
├── kdf_salt         bytes(16)                 salt do Argon2id do navegador (sempre existe)
├── auth_hash        str                       Argon2(auth_key), calculado no servidor (sempre existe)
├── created_at       datetime                  (UTC, sem fuso no banco)
└── expires_at       datetime                  (indexado, para a limpeza)

Campos que entram só quando forem usados: last_activity_at (Fase 6, se a limpeza precisar).
O limite de 500 MB por sala vem da configuração (MAX_ROOM_SIZE_MB), não de uma coluna.

StoredFile (arquivo)
├── id               UUID (PK)                 também é o nome no disco
├── room_id          FK → Room (on delete cascade)
├── encrypted_meta   bytes                     nome, MIME e tamanho original, criptografados
├── size_bytes       int                       tamanho do .bin criptografado (para os limites)
└── created_at       datetime

(uploaded_by, o apelido criptografado do dispositivo, entra na Fase 4 junto com a lista de dispositivos.)

RoomText (editor compartilhado, 1 por sala)
├── room_id          FK → Room (PK)
├── ciphertext       bytes                     (limite ex.: 1 MB)
├── version          int                       incrementa a cada alteração
└── updated_at       datetime

Clip (textos colados)
├── id               UUID (PK)
├── room_id          FK → Room (on delete cascade)
├── ciphertext       bytes                     (limite ex.: 64 KB cada, até 200 por sala)
└── created_at       datetime
```

Disco: `storage/{room_id}/{file_id}`. Apagar a sala = apagar a pasta inteira + registros (cascade).

---

## 8. API (endpoints)

### REST

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/rooms` | Cria sala. Body: `{ttl_hours, has_password, kdf_salt?, auth_key?}` → `{code, expires_at}` + cookie de sessão. **A senha nunca é enviada**, só o `auth_key` derivado dela. |
| `GET` | `/api/rooms/{code}/params` | Antes de entrar: `{has_password, kdf_salt}` para o navegador derivar as chaves (com rate limit) |
| `POST` | `/api/rooms/{code}/join` | Entra na sala. Body: `{auth_key?}` → cookie de sessão |
| `GET` | `/api/rooms/{code}` | Info da sala (expiração, uso de espaço, dispositivos online) |
| `DELETE` | `/api/rooms/{code}` | Encerra a sala e apaga tudo |
| `POST` | `/api/rooms/{code}/leave` | Sai (apaga cookie) |
| `GET` | `/api/rooms/{code}/files` | Lista arquivos |
| `POST` | `/api/rooms/{code}/files` | Upload de **um arquivo já criptografado**: o corpo da requisição é o arquivo (lido em streaming, sem `python-multipart`) e o cabeçalho `X-File-Meta` leva o nome, tipo e tamanho originais, criptografados. Erro `413` com `file_too_large` ou `room_full` |
| `GET` | `/api/rooms/{code}/files/{file_id}` | Download do `.bin` criptografado (o navegador descriptografa) |
| `DELETE` | `/api/rooms/{code}/files/{file_id}` | Exclui arquivo |
| `GET` | `/api/rooms/{code}/text` | Texto criptografado atual + versão (`ciphertext` vazio e versão 0 enquanto ninguém escreveu) |
| `PUT` | `/api/rooms/{code}/text` | Salva o texto `{ciphertext, base_version}`. Só aceita se `base_version` for a versão atual; senão `409` com `{"code": "text_conflict", "current": {ciphertext, version}}`. `413` com `text_too_large` |
| `GET` | `/api/rooms/{code}/clips` | Lista clips (criptografados) |
| `GET` / `PUT` | `/api/rooms/{code}/source` | O **código compartilhado**: igual ao `/text` (versão, `409` em conflito), em outra tabela |
| `GET` / `POST` / `DELETE` | `/api/rooms/{code}/code-clips[/{id}]` | Os **blocos de código**: iguais aos clips, em outra tabela e com limite maior (256 KB cada) |
| `POST` | `/api/rooms/{code}/clips` | Cria clip `{ciphertext}`. `413` com `clip_too_large` ou `clips_full` |
| `DELETE` | `/api/rooms/{code}/clips/{clip_id}` | Exclui clip |

Campos binários (`ciphertext`, `kdf_salt`, `encrypted_meta`, `auth_key`) trafegam em JSON como **base64url**.

### WebSocket: `/ws/rooms/{code}`
Autenticado pelo cookie. Mensagens em JSON com campo `type`:

**Servidor → cliente**
```json
{"type": "file_added",    "file": {"id": "...", "encrypted_meta": "...", "size_bytes": 204800, "created_at": "..."}}
{"type": "file_deleted",  "file_id": "..."}
{"type": "text_updated",  "ciphertext": "...", "version": 13}
{"type": "clip_added",    "clip": {"id": "...", "ciphertext": "..."}}
{"type": "clip_deleted",  "clip_id": "..."}
{"type": "source_updated", "ciphertext": "...", "version": 4}
{"type": "code_clip_added",   "clip": {...}}
{"type": "code_clip_deleted", "clip_id": "..."}
{"type": "presence",      "online": 2}
{"type": "room_closed",   "reason": "expired"}
```

**Cliente → servidor**
```json
{"type": "ping"}                       (o servidor responde {"type": "pong"})
```

O texto e os clips são **gravados pela API REST** (`PUT /text`, `POST /clips`), que valida, guarda e então avisa os aparelhos pelo WebSocket. Assim todo erro (conflito, tamanho, sessão) chega como resposta HTTP normal. Não existe mensagem `init`: ao abrir (e ao reabrir) a conexão, o navegador recarrega o estado pela API REST, que já é a fonte da verdade. A conexão só avisa o que muda.

O servidor só repassa esses campos; ele não consegue ler o conteúdo.

O cliente **reconecta sozinho** se a conexão cair (backoff: 1s, 2s, 4s… até 30s) e recarrega o estado atual ao reconectar. Isso é essencial no celular, que derruba conexões quando a tela apaga.

---

## 9. Front-end

**Decidido:** HTML renderizado pelo FastAPI com **Jinja2** + **JavaScript puro** (sem React/Vue). O app tem 2 telas, e um framework JS só adicionaria build e complexidade. CSS com **Pico.css** (arquivo local, para funcionar sem internet na rede local).

### Telas
1. **Início (`/`)**: duas abas.
   - **Criar sala:** tempo de expiração (1h / **12h** / 24h / 48h), checkbox "proteger com senha" (mínimo 6 caracteres) e apelido do dispositivo.
   - **Entrar:** código; se a sala tiver senha, o campo de senha aparece em seguida.
   - Lembra a última sala via localStorage (só o código, nunca a chave).
2. **Sala (`/r/{code}`)**:
   - Topo: código da sala (com botão copiar), **botão "QR Code / link"**, tempo restante, dispositivos online, botão "encerrar", ícone de cadeado "criptografado".
   - Área de arquivos: zona de arrastar e soltar, botão de seleção, lista com nome/tamanho/quem enviou/botões baixar e excluir, barra de progresso nos envios ("criptografando…" → "enviando…").
   - Editor de texto: `<textarea>` grande com botões "copiar tudo" e "limpar"; indicador "sincronizado ✓ / sincronizando…".
   - Clips: campo "colar texto" + lista de cartões, cada um com "copiar" e "excluir".
   - No celular: as áreas viram abas ("Arquivos" | "Texto" | "Clips").

### Detalhes que fazem diferença na usabilidade
- **Ctrl+V de imagem** (print da tela) em qualquer lugar da sala → vira upload automático.
- **Ctrl+V de texto** fora do editor → vira um clip.
- Progresso de upload com `XMLHttpRequest.upload.onprogress` (o `fetch` ainda não tem isso de forma simples).
- Notificação sutil/toast quando chega arquivo novo de outro dispositivo.
- Campo de código com auto-maiúsculas e aceitando com ou sem hífen.

### Módulos JS
```
static/js/
├── vendor/
│   ├── sodium.js     # libsodium-wrappers-sumo (arquivo local, com SRI)
│   └── qrcode.js     # gerador de QR Code
├── crypto.js     # derivar chaves, criptografar/descriptografar arquivos (stream) e textos
├── api.js        # chamadas REST (fetch / XHR com progresso)
├── socket.js     # WebSocket com reconexão automática
├── files.js      # lista, upload, drag-and-drop, colar imagem
├── editor.js     # textarea, debounce, versão, aviso de conflito
├── clips.js      # criar, listar, copiar e excluir clips
└── room.js       # junta tudo na página da sala
```

`crypto.js` é a peça mais crítica: deve ser pequeno, bem testado e o **único** lugar que toca em chaves.

---

## 10. Estrutura de pastas

```
Transferência de Arquivos/
├── backend/                     # tudo que é Python
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # cria o FastAPI, liga rotas, serve o frontend, lifespan
│   │   ├── config.py            # configurações via pydantic-settings (backend/.env)
│   │   ├── database.py          # engine/sessão SQLAlchemy async
│   │   ├── models.py            # Room, StoredFile, RoomText, Clip
│   │   ├── schemas.py           # modelos Pydantic de entrada/saída
│   │   ├── security.py          # Argon2 do auth_key, geração de código, token de sessão, rate limit
│   │   ├── storage.py           # salvar/ler/apagar arquivos no disco (interface trocável p/ S3)
│   │   ├── realtime.py          # ConnectionManager (salas → websockets, broadcast)
│   │   ├── cleanup.py           # loop que apaga salas expiradas
│   │   └── routers/
│   │       ├── pages.py         # rotas HTML (/, /r/{code})
│   │       ├── rooms.py         # criar/entrar/sair/encerrar
│   │       ├── files.py         # upload/download/excluir
│   │       ├── clips.py         # criar/listar/excluir clips
│   │       └── ws.py            # endpoint WebSocket
│   ├── tests/
│   ├── storage/                 # arquivos enviados (no .gitignore)
│   ├── .env.example
│   ├── pyproject.toml           # configuração do pytest e do ruff
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                    # tudo que roda no navegador
│   ├── templates/               # Jinja2: base.html, index.html, room.html
│   └── static/
│       ├── css/style.css
│       └── js/ (vendor/, crypto.js, api.js, socket.js, files.js, editor.js, clips.js, room.js)
├── CLAUDE.md                    # regras do projeto
├── PLANEJAMENTO.md
├── README.md
└── .gitignore
```

---

## 11. Dependências

```text
fastapi                # framework web
uvicorn[standard]      # servidor ASGI (inclui suporte a websockets)
python-multipart       # upload de arquivos (multipart/form-data)
jinja2                 # templates HTML
sqlalchemy[asyncio]    # ORM  (ou sqlmodel, que é SQLAlchemy + Pydantic juntos)
aiosqlite              # driver SQLite assíncrono
aiofiles               # escrita/leitura de arquivo assíncrona
argon2-cffi            # hash do auth_key (o servidor nunca vê a senha)
itsdangerous           # cookie de sessão assinado
pydantic-settings      # configuração via .env

# desenvolvimento
pytest
pytest-asyncio
httpx2                 # cliente de teste (o Starlette atual pede httpx2 no lugar do httpx)
ruff                   # lint/format
```

**Bibliotecas JavaScript** (baixadas uma vez e servidas de `static/js/vendor/`, sem CDN):
- `libsodium-wrappers-sumo`: criptografia (a versão *sumo* é necessária porque inclui o `crypto_pwhash`/Argon2id)
- `qrcode-generator` (ou similar): QR Code com o link da sala
- `pico.css`: estilo

Opcionais depois: `redis`, `boto3` (S3/R2), `pycrdt` (Yjs).

> Observação: você está com **Python 3.14**. Se alguma biblioteca der erro de instalação (rodas ainda não publicadas), use um ambiente virtual com Python 3.12 ou 3.13.

---

## 12. Configurações (`.env`)

```ini
SECRET_KEY=troque-por-um-valor-aleatorio-longo
DATABASE_URL=sqlite+aiosqlite:///./quickdrop.db
STORAGE_DIR=./storage
MAX_FILE_SIZE_MB=100
MAX_ROOM_SIZE_MB=500
ALLOWED_TTL_HOURS=1,12,24,48
DEFAULT_TTL_HOURS=12
MAX_TEXT_SIZE_KB=1024
MAX_CLIP_SIZE_KB=64
MAX_CLIPS_PER_ROOM=200
CLEANUP_INTERVAL_MINUTES=5
LOGIN_RATE_LIMIT=5/minute
COOKIE_SECURE=false        # true quando estiver em HTTPS (internet)
```

O mesmo código roda local e na internet; só muda o `.env`.

---

## 13. Roteiro de desenvolvimento (fases)

### Fase 0: Preparação (½ dia) ✅
- [x] Criar ambiente virtual e `requirements.txt`
- [x] `git init`, `.gitignore` (venv, `storage/`, `*.db`, `.env`)
- [x] FastAPI "olá mundo" rodando com `uvicorn app.main:app --reload`
- [x] Estrutura de pastas e `config.py`

### Fase 1: Criptografia no navegador (2 dias) ✅
Vem antes de tudo porque todas as outras partes dependem dela.
- [x] Baixar a libsodium (`libsodium-wrappers-sumo` 0.8.4, versão ESM) para `frontend/static/js/vendor/`
- [x] `crypto.js`: derivar chaves (Argon2id + KDF), gerar salt e segredo aleatórios, `encryptText`/`decryptText`, `encryptJson`/`decryptJson`, `encryptFile`/`decryptFile` em blocos de 1 MB, codificação base64url
- [x] 27 testes em `frontend/tests/` (`npm test` ou `node --test`): ida e volta, chave errada, dado adulterado, arquivo cortado ou com dados extras, conteúdo cifrado sem o texto original
- [x] Página `/dev/crypto` (só com `DEBUG=true`) que mede o Argon2id e testa texto e arquivo no navegador
- [ ] Medir o Argon2id num celular de verdade (no PC leva ~130 ms; o alvo é até ~1 s) e ajustar os parâmetros se precisar

### Fase 2: Salas (2 dias) ✅
- [x] Modelo `Room` e banco SQLite criado no startup (SQLAlchemy assíncrono; trocar a URL basta para usar PostgreSQL)
- [x] Código aleatório seguro (`secrets`, alfabeto sem caracteres ambíguos); Argon2 do `auth_key` no servidor, em outra thread
- [x] `POST /api/rooms`, `GET /api/rooms/{code}/params`, `POST /api/rooms/{code}/join` e `GET /api/rooms/{code}`, com cookie de sessão assinado (um por sala, `HttpOnly`, `SameSite=Strict`)
- [x] Dependência `get_current_room()` que valida o cookie nas rotas protegidas
- [x] Segredo gerado vai no fragmento `#k=...` do link e do QR Code; o código completo para digitar é `K7P3XM-HQ4T-9WZC`
- [x] Telas: início (criar e entrar com o mesmo peso) e página da sala (código, link, QR Code, tempo restante), em português e inglês, claro e escuro, com o mundo visual "Linhas de Metrô" (Impeccable)
- [x] 31 testes no backend (criar, entrar, senha errada, sala inexistente, TTL inválido, cookie falso, sala expirada) e 35 no frontend
- Fica para depois: apelido do dispositivo e lista de dispositivos online (Fase 4), limite de tentativas no `/params` e no `/join` (Fase 6), botão "encerrar sala" (Fase 6)

### Fase 3: Arquivos, sem tempo real ainda (2–3 dias) ✅
- [x] `storage.py`: grava em streaming (sem carregar o arquivo na memória), confere o tamanho durante o envio e apaga o que sobrar se passar do limite; arquivos no disco com nome UUID
- [x] Rotas: enviar, listar, baixar (sempre como anexo, `nosniff`) e excluir; só quem entrou na sala; arquivo de outra sala devolve 404
- [x] Limites: 100 MB por arquivo (com 1 MB de folga para o acréscimo da criptografia) e 500 MB por sala, somando todos os arquivos; todo tipo de arquivo é aceito
- [x] Front: criptografa antes de enviar (fila, um por vez), barra de progresso amarela (em trânsito), arrastar e soltar, seleção múltipla, lista com nomes descriptografados, baixar (descriptografa no navegador) e excluir com confirmação
- [x] 58 testes no backend (incluindo limites, sala cheia, cookie falso, arquivo de outra sala e sala expirada) e 40 no frontend
- [x] Verificado no navegador com dois "aparelhos": arquivo de texto, binário de 2,5 MB com extensão rara e arquivo vazio voltaram idênticos; no disco só há bytes embaralhados
- Fica para a Fase 4: a lista dos outros aparelhos só atualiza ao recarregar a página (o tempo real chega com o WebSocket)

### Fase 4: Tempo real (2 dias) ✅
- [x] `ConnectionManager` na memória (sala → conexões), com aviso a todos quando alguém entra ou sai; conexão que falha ao enviar é descartada sem derrubar as outras
- [x] Endpoint WebSocket `/ws/rooms/{code}`: só entra quem tem o cookie da sala; recusa páginas de outros sites (cabeçalho `Origin`), sala inexistente e mensagem que não é JSON
- [x] Upload e exclusão de arquivo avisam todos os aparelhos da sala (`file_added`, `file_deleted`)
- [x] `socket.js` com reconexão automática (1s, 2s, 4s… até 30s) e `ping` a cada 25s; ao reconectar a lista é reconciliada com o servidor
- [x] Presença: o diagrama da rota mostra "Conectado" (ponto verde) quando há outro aparelho, e "Sem conexão. Reconectando..." quando este aparelho cai
- [x] 73 testes no backend (16 de tempo real, incluindo acesso negado) e 42 no frontend
- [x] Verificado no navegador com duas abas: envio e exclusão aparecem no outro aparelho sem recarregar, presença sobe e desce, e depois de reiniciar o servidor a aba reconectou sozinha e mostrou um arquivo enviado durante a queda
- [ ] **Teste de verdade:** PC + celular na mesma rede Wi-Fi (com o celular que apaga a tela)
- Fica para depois: nomes dos aparelhos (hoje só a contagem), e o aviso `room_closed` ao expirar (Fase 6)

### Fase 5: Editor de texto e clips (2 dias) ✅
- [x] Modelos `RoomText` (com versão) e `Clip`; o texto é criado vazio (versão 0) na primeira consulta
- [x] `PUT /text` com versão: a conferência e a troca são uma única instrução do banco, então duas edições ao mesmo tempo nunca passam as duas; quem perde recebe `409` com o texto atual
- [x] Avisos ao vivo `text_updated`, `clip_added` e `clip_deleted`
- [x] Editor: salva ~600 ms depois de parar de digitar, mostra "Salvando... / Sincronizado", salva também quando a aba vai para o fundo, copiar tudo e limpar (com confirmação), mantém o cursor quando chega texto de outro aparelho
- [x] Conflito: se chega texto de outro aparelho enquanto há alterações suas, aparece um aviso com "Usar a do outro aparelho" ou "Manter a minha"; o eco do próprio salvamento é reconhecido e não gera aviso
- [x] Clips: caixa para colar e guardar, lista com o mais novo no alto, copiar e excluir (com confirmação), e **Ctrl+V fora de qualquer campo vira clip**; limites de 64 KB por clip e 200 por sala
- [x] Limites: texto de 1 MB (antes de criptografar); mensagens de erro com o tamanho, em português e inglês
- [x] Navegação rápida na sala (Arquivos, Texto, Convidar) para o celular
- [x] 95 testes no backend e 42 no frontend
- [x] Verificado no navegador com duas abas: texto nos dois sentidos, conflito provocado (a escolha "Manter a minha" chegou ao outro aparelho), clips ao vivo, Ctrl+V global, exclusão com confirmação, limite de 64 KB; no banco não aparece nenhum texto original
- Fica para depois: edição simultânea sem conflito (CRDT/Yjs), se algum dia for preciso

### Fase 6: Expiração e robustez (1 dia) ✅
- [x] Limpeza automática: ao iniciar e a cada `CLEANUP_INTERVAL_MINUTES` (5 por padrão) o servidor apaga as salas expiradas, com arquivos no disco, texto, clips e registros
- [x] `room_closed` (`expired` ou `closed`) avisa e fecha as conexões de quem está na sala; o navegador mostra "Sala encerrada", esquece a chave e para de reconectar; ao chegar a zero a contagem regressiva também encerra a tela
- [x] Botão "Encerrar sala" (com confirmação) e `DELETE /api/rooms/{code}`. Na Fase 6 qualquer aparelho que entrasse podia encerrar; **agora só o dono** (veja "Dono da sala" abaixo)
- [x] Limite de tentativas feito à mão (`rate_limit.py`, sem biblioteca): senhas erradas (5 por minuto por IP e sala; enquanto bloqueado até a senha certa é recusada), consultas e entradas (30 por minuto por IP) e salas criadas (20 por hora por IP); `429` com `Retry-After`
- [x] Cabeçalhos de segurança em toda resposta: CSP (só código, estilos e fontes do próprio servidor; `wasm-unsafe-eval` para a criptografia), `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` (o código da sala está no endereço), `Permissions-Policy`, `Cache-Control: no-store` na API e HSTS quando `COOKIE_SECURE=true`
- [x] 125 testes no backend (30 novos) e 42 no frontend
- [x] Verificado no navegador: com a CSP ligada nada quebrou (WebAssembly, WebSocket, QR Code, cópia, upload); encerrar numa aba mostra "Sala encerrada" na outra e esvazia o disco; o bloqueio por excesso de tentativas aparece em português
- Não feito: SRI nos scripts (os scripts são do próprio servidor, a CSP já impede código de fora; SRI só agregaria algo se um dia vierem de CDN). Atrás de um proxy (Fase 8), iniciar o servidor com `--proxy-headers` para o limite enxergar o IP verdadeiro

### Fase 7: Polimento ✅
- [x] **Colar imagem com Ctrl+V** em qualquer lugar da sala vira envio; prints (que chegam como "image.png") ganham o nome `captura-AAAAMMDD-HHMMSS.png`; arquivos copiados do computador mantêm o nome; texto colado continua virando clip
- [x] **Pré-visualização de imagens** na lista ("Ver" / "Ocultar"): baixa e descriptografa só quando a pessoa pede, mostra na própria linha e libera a memória ao ocultar. Só PNG, JPEG, GIF, WebP, AVIF e BMP de até 20 MB; **SVG e HTML nunca** (podem conter script)
- [x] **Baixar tudo em .zip**: zip criado no navegador, sem biblioteca e sem compressão (fotos, PDFs e vídeos já são comprimidos), com nomes em UTF-8, nomes repetidos numerados e a data de cada arquivo; aparece com 2 ou mais arquivos. Conferido com o `zipfile` do Python (soma de verificação de cada arquivo confere)
- [x] **Tema escuro**: já existia desde a Fase 2 (segue o aparelho)
- [x] **PWA instalável**: manifesto, ícones (um "Q" branco sobre azul de linha com cauda amarela, incluindo versão "maskable" para Android e ícone da Apple), cor da barra do navegador clara e escura, e service worker que só mostra uma página de "sem conexão" quando o servidor não responde. De propósito não guarda salas, arquivos nem API em cache
- [x] Arquivos de `/static` agora são revalidados a cada uso (`Cache-Control: no-cache` + `ETag`): sem isso, o navegador reaproveitava JavaScript antigo depois de uma atualização
- [x] 132 testes no backend e 57 no frontend
- [x] Verificado no navegador: imagem colada virou arquivo, a imagem apareceu decifrada (120x80), o SVG não ganhou botão "Ver", o zip tinha os 3 arquivos em ordem, o service worker registrou com escopo `/` e a página "Sem conexão" apareceu com o servidor desligado
- Não feito: "Compartilhar com…" do Android (share target). Exige escolher para qual sala o conteúdo vai e tratar arquivos por um service worker; fica como ideia futura
- Ícones: gerados por script com a biblioteca Pillow (um "Q" desenhado com formas simples, sem imagem de terceiros)

### Extra (pedido depois da Fase 7): código compartilhado e blocos de código ✅
Para passar trechos de código sem perder a formatação, a sala ganhou um editor de código e uma lista de blocos de código, ao lado dos de texto.
- [x] **Campo de código** (`/source`, ao vivo, com conflito por versão, igual ao texto): fonte monoespaçada do sistema, sem quebra de linha (rola para o lado), tabulação de 4 colunas, **sem ligaduras** (o `=>` aparece como dois caracteres, exatamente o que será copiado) e sem autocorreção, corretor ou maiúscula automática (no celular o teclado trocava aspas retas por curvas, o que quebra o código)
- [x] **Tab indenta e Shift+Tab tira a indentação** (4 espaços; com várias linhas selecionadas, todas). Para o teclado não ficar preso no campo: **Esc e depois Tab** move o foco. O "desfazer" (Ctrl+Z) continua funcionando
- [x] **Blocos de código** (`/code-clips`): caixa para colar, lista com o mais novo no alto, **Copiar** que entrega exatamente o que foi guardado (tabs, espaços no fim da linha, acentos), excluir com confirmação; até 256 KB por bloco e 200 por sala, contados à parte dos clips de texto
- [x] Colar fora de qualquer campo (Ctrl+V) continua virando **clip de texto**: o app não tem como saber se o que foi colado é código
- [x] Sem realce de sintaxe, por decisão: exigiria uma biblioteca de terceiros e dá para acrescentar depois sem mexer no resto
- [x] Tabelas **novas** no banco (`room_source_code`, `code_clips`): o banco existente continua funcionando sem migração
- [x] Código reaproveitado em vez de copiado: no backend, `create_document_router` e `create_clips_router` montam as rotas do texto e do código; no frontend, `shared-editor.js` e `clips-panel.js` servem aos dois, e `room-panels.js` liga todos os painéis
- [x] 148 testes no backend e 68 no frontend (a indentação tem testes próprios)
- [x] Verificado no navegador com duas abas: código com tabulação, espaços no fim da linha, crases e acentos chegou idêntico ao outro aparelho; o bloco salvo apareceu ao vivo, foi copiado exatamente e excluído com confirmação; Tab, Shift+Tab e Esc+Tab se comportaram como descrito

### Extra (depois da Fase 8): dono da sala ✅
Antes, qualquer convidado podia encerrar a sala. Agora só quem a criou pode.
- [x] **Cookie de dono** (`owner_{código}`): assinado, `HttpOnly`, `SameSite=Strict`, vale até a sala expirar. Só o navegador que **cria** a sala o recebe; entrar pelo link, QR Code ou senha nunca dá esse cookie
- [x] O cookie guarda o **id interno da sala**, não o código, e usa um "sal" próprio: nem um token de participante nem o de dono de outra sala valem como dono desta
- [x] `DELETE /api/rooms/{code}` de um convidado responde **403** (`not_owner`); sem ter entrado continua 401
- [x] `GET` e `join` da sala devolvem `is_owner`; a tela mostra o botão só ao dono, e ao convidado mostra o aviso de que a sala some sozinha quando o tempo acabar
- [x] Convidados continuam enviando, apagando arquivos, clips e texto (a sala é um espaço compartilhado, decisão do Gabriel)
- [x] Sem mudança no banco: nada de coluna nova nem migração
- Limitação: o dono é o **navegador** que criou. Criar no PC e abrir no celular pelo QR Code faz do celular um convidado; limpar os cookies do PC tira o poder de encerrar (a sala ainda expira sozinha). Salas criadas antes desta atualização ficam sem dono
- [x] 164 testes no backend (7 novos) e 68 no frontend; conferido no navegador com dois "aparelhos" (`localhost` dono, `127.0.0.1` convidado)

### Fase 8: Internet (no ar em https://quickdrop-syoti.mexicocentral.cloudapp.azure.com; celular na 4G funcionou)
Hospedagem **grátis**, explicada na seção 14.1. Resumo: **Oracle Cloud Always Free** (uma VM Ubuntu de verdade, ligada 24 h) com **Docker + Caddy** e um endereço grátis do **DuckDNS**.

**8a. Preparar o app para a internet (no PC, com testes)**
- [x] **IP verdadeiro atrás do Caddy**: iniciar o Uvicorn com `--proxy-headers --forwarded-allow-ips=<IP do Caddy>`. Sem isso, todos os visitantes parecem ter o IP do Caddy e o limite de tentativas bloquearia todo mundo junto
- [x] **Limite global de disco** (`MAX_TOTAL_STORAGE_GB`, ex.: 30): sem ele, uma pessoa criando 20 salas por hora com 500 MB cada enche o disco grátis em poucas horas. Ao passar do limite, o envio responde `507` com mensagem clara ("O servidor está cheio agora")
- [x] **Limite de salas ativas** (`MAX_ACTIVE_ROOMS`, ex.: 500), pelo mesmo motivo
- [x] Página `/sobre` curta: o que o QuickDrop guarda (nada legível), por quanto tempo, e um contato para denúncia de abuso. Como tudo é criptografado, a única resposta possível a uma denúncia é encerrar a sala
- [x] Testes para os limites globais (157 testes no backend) e conferência do IP vindo do proxy com o Uvicorn de verdade: 30 consultas de um IP e a 31ª bloqueada, enquanto outro IP seguia livre; `/sobre` com testes próprios

**8b. Empacotar**
- [x] `Dockerfile` (Python slim, usuário sem privilégios, **1 worker** do Uvicorn: as conexões em tempo real e os limites de tentativas ficam na memória do processo)
- [x] `docker-compose.yml` com dois serviços: `app` (só visível dentro do Docker) e `caddy` (portas 80 e 443)
- [x] `Caddyfile`: HTTPS automático (Let's Encrypt), `request_body max_size 110MB`, WebSocket passa sem configuração extra
- [x] **Volume persistente** `quickdrop-data` com o banco SQLite e a pasta `storage/` (sobrevive a atualizações). Continua SQLite: um único servidor não precisa de PostgreSQL
- [x] `.env` de produção fora do Git: `SECRET_KEY` nova, `DEBUG=false` (desliga `/dev/crypto`), `COOKIE_SECURE=true` (liga também o HSTS)
- [x] Testado com `docker compose up` no PC (`DOMAIN=localhost`): imagem construída, app saudável e rodando sem privilégios, HTTPS e redirecionamento 80→443 pelo Caddy, cookie `Secure` e HSTS, `/sobre` com o contato, arquivo de 100 MB enviado com sucesso e um de 111 MB recusado pelo Caddy (413), WebSocket por `wss://` entregando a presença, arquivos preservados depois de `docker compose down` e `up` (volume persistente)

**8c. Servidor (feito por você, seguindo o `DEPLOY.md`, que já está escrito)**
- [ ] Criar a conta na Oracle Cloud, região **São Paulo** ou **Vinhedo** (a região de origem não pode ser trocada depois e os recursos grátis só existem nela)
- [ ] Criar a VM **Ampere A1** (1 OCPU e 6 GB já sobram; o limite grátis é 2 OCPU e 12 GB) com Ubuntu e disco de 50 GB
- [ ] Abrir as portas 80 e 443 em **dois lugares**: na "Security List" da Oracle e no firewall do próprio Ubuntu (a imagem da Oracle vem com `iptables` bloqueando; é o erro mais comum)
- [ ] Criar o subdomínio no DuckDNS (ex.: `quickdrop-gabriel.duckdns.org`) apontando para o IP público da VM
- [ ] Instalar Docker, clonar o repositório, criar o `.env`, `docker compose up -d`
- [ ] SSH só com chave, atualizações de segurança automáticas (`unattended-upgrades`)

**8d. Conferir na internet**
- [ ] Cadeado do HTTPS, nota dos cabeçalhos de segurança, cookie com `Secure`
- [ ] Teste com **celular no 4G** e PC em outra rede: sala, arquivo de 100 MB, texto ao vivo, celular com a tela apagada e voltando
- [ ] Argon2id no celular abaixo de ~1 s (pendência da Fase 1)
- [ ] Atualizar o app depois: `git pull && docker compose up -d --build` (descrito no `DEPLOY.md`)

**Resultado do servidor (Azure for Students, em vez da Oracle):** a Oracle recusou os cartões; a Microsoft liberou o crédito de estudante, mas só em 5 regiões. VM `Standard_B2ats_v2` no **México Central**, Ubuntu 24.04, Docker + Caddy, endereço do próprio Azure. Conferido pela internet: certificado Let's Encrypt válido, redirecionamento 80 para 443, HSTS, IP real do visitante nos registros (o `--proxy-headers` funciona), sala criada, arquivo de 20 MB enviado e baixado, sala encerrada. Celular na 4G testado pelo Gabriel: funcionou. Pendente: arquivo de 100 MB, tempo do Argon2id no celular e tela apagada.

**Fora desta fase, de propósito:** domínio pago, CDN, backup (as salas duram no máximo 48 h), deploy automático pelo GitHub, vários servidores.

**Total estimado do MVP (fases 0 a 6):** cerca de 2 a 3 semanas em ritmo de estudo. A criptografia acrescenta uns 3 a 4 dias em relação ao plano original.

---

## 14. Onde rodar (deploy)

| Opção | Como | Prós | Contras |
|---|---|---|---|
| **Rede local (comece por aqui!)** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` e acessar `http://IP-DO-PC:8000` no celular | Grátis, super rápido (velocidade do Wi-Fi), arquivos não saem de casa | Só funciona na mesma rede e com o PC ligado; liberar a porta no Firewall do Windows |
| **VPS** (Hetzner, DigitalOcean, Oracle Free Tier) | Docker + Caddy (HTTPS automático) na frente do Uvicorn | Controle total, disco persistente, barato | Você administra o servidor |
| **PaaS** (Railway, Render, Fly.io) | Deploy pelo GitHub | Fácil, HTTPS pronto | Em planos grátis o **disco costuma ser apagado** a cada deploy/reinício: precisa de volume persistente ou S3/R2 |

**Decidido:** desenvolver e usar na **rede local** primeiro. Depois, para acessar de qualquer lugar, subir numa VPS com Docker + Caddy (Fase 8).

### 14.1 Hospedagem grátis (pesquisa de outubro de 2026)

O QuickDrop precisa de quatro coisas que eliminam a maioria das opções grátis: **ficar ligado** (WebSocket aberto e a limpeza das salas a cada 5 min), **disco que não some** (arquivos e banco), **envios de até ~101 MB** (100 MB mais a criptografia) e **muito tráfego de saída** (cada arquivo é baixado por outro aparelho).

| Opção | Ligado 24 h | Disco persistente | Envio de 100 MB | Veredito |
|---|---|---|---|---|
| **Oracle Cloud Always Free** (VM ARM, 2 OCPU / 12 GB, 200 GB de disco, 10 TB de saída/mês) | Sim | Sim | Sim | ✅ **Escolhida** |
| Google Cloud e2-micro | Sim | Sim (30 GB) | Sim | ❌ só 1 GB de saída grátis por mês e só nos EUA |
| Render (grátis) | Dorme após 15 min | Não | Sim | ❌ derruba o tempo real e apaga os arquivos |
| Fly.io, Railway, Koyeb | Só teste ou crédito de US$ 1 | — | — | ❌ não têm mais plano grátis de verdade |
| Hugging Face Spaces | Dorme | Não (pago) | Sim | ❌ e não é feito para isso |
| **PC de casa + Cloudflare Tunnel** | Só com o PC ligado | Sim (o seu) | **Não**: o plano grátis corta envios acima de 100 MB (erro 413) | ⚠️ só serviria baixando o limite para ~95 MB |
| **PC de casa + Tailscale Funnel** | Só com o PC ligado | Sim | Sim | ⚠️ **plano B** sem cartão; endereço `*.ts.net` com HTTPS pronto |

**Cuidados com a Oracle:**
- Pede **cartão de crédito só para verificar** a identidade; no plano "Always Free" não há cobrança. Não ativar recursos fora da lista grátis.
- Em junho de 2026 a Oracle **reduziu** a cota ARM de 4 OCPU/24 GB para 2 OCPU/12 GB, sem aviso. Ainda sobra muito para o QuickDrop, mas mostra que as regras podem mudar: o Docker deixa a mudança para outro servidor simples.
- A Oracle pode **recuperar VMs grátis paradas** (uso de CPU muito baixo por dias). O tráfego normal e a limpeza periódica ajudam; se acontecer, recriar a VM leva uns 20 minutos com o guia.
- Às vezes a região está **sem capacidade ARM** ("Out of capacity"): tentar de novo mais tarde ou usar a VM AMD micro grátis (1 GB de RAM, também serve).

**Endereço grátis:** o **DuckDNS** dá um subdomínio (`algo.duckdns.org`) que aponta para o IP da VM, e o Caddy consegue o certificado HTTPS para ele sozinho. Um domínio próprio (~R$ 40/ano) pode substituir depois sem mexer no código.

**Cuidados da fase local (HTTP via IP):**
- `navigator.clipboard` e `crypto.subtle` só funcionam em **HTTPS ou localhost**. Por isso a criptografia usa a libsodium.js (funciona em HTTP) e o botão copiar terá fallback com `document.execCommand('copy')`.
- Em HTTP na rede local, alguém na mesma rede poderia, em tese, alterar o JavaScript em trânsito. Na sua casa isso é aceitável; na internet, **HTTPS é obrigatório**.
- Liberar a porta 8000 no Firewall do Windows (rede privada).

---

## 15. Testes

- **pytest + httpx `AsyncClient`** para as rotas REST.
- **`TestClient.websocket_connect`** do FastAPI para testar os eventos: conectar dois clientes na mesma sala, fazer upload por um e verificar se o outro recebe `file_added`.
- Banco SQLite em memória e pasta `storage` temporária (`tmp_path`) nos testes.
- Nos testes do servidor, o conteúdo é só bytes opacos; o servidor não precisa (nem deve) saber criptografar.
- **Teste de segurança importante:** confirmar que nenhum dado em texto puro chega ao servidor (inspecionar o banco e a pasta `storage/` depois de enviar um arquivo e um texto conhecidos).
- A criptografia é testada na página `/dev/crypto` (Fase 1): ida e volta de textos e arquivos, arquivo adulterado deve falhar, chave errada deve falhar.
- Teste manual sempre com **dois dispositivos reais** (PC + celular).

---

## 16. Decisão: como entrar numa sala **sem senha** com E2E

> ✅ **Decidido: A + C.** QR Code/link como caminho principal e código longo (`K7P3XM-HQ4T-9WZC`) como alternativa para digitar.

A combinação "senha opcional" + "criptografia desde o início" cria um ponto a decidir: se não há senha, de onde vem a chave?

| Opção | Como funciona | Prós | Contras |
|---|---|---|---|
| **A. Chave no link/QR (recomendada)** | Chave aleatória no fragmento `#k=...`. Entra-se pelo QR Code ou pelo link | E2E de verdade: o servidor nunca tem a chave | Digitar **só o código** no outro aparelho não basta; precisa do QR ou do link |
| B. Chave derivada do código | A chave sai do próprio código da sala | Basta digitar o código | **Não é E2E de verdade**: o servidor conhece o código e conseguiria ler tudo. Seria só "criptografia em repouso" |
| C. Código mais longo | Sala sem senha mostra um código maior, ex. `K7P3XM-HQ4T-9WZC`, em que a 2ª parte é a chave | Dá para digitar; E2E de verdade | Código de 14 caracteres; é praticamente uma senha gerada automaticamente |

**Recomendação: A + C juntas.** QR Code/link como caminho principal (no celular é só apontar a câmera) e o código longo como alternativa para digitar quando não houver câmera. Assim toda sala é E2E de verdade, e a senha opcional vira "quero escolher minha própria senha em vez de usar a gerada".

**Detalhe técnico do código longo:** a 1ª parte (6 caracteres) é o código da sala, enviado ao servidor; a 2ª parte (8 caracteres, ~40 bits) é um segredo que nunca vai ao servidor. Ele passa pelo mesmo Argon2id de uma senha, gerando `auth_key` e `enc_key`. Ou seja, internamente **toda sala tem senha**: ou escolhida pelo usuário, ou gerada pelo app. O QR Code/link carrega esse segredo no fragmento `#k=...`. Com isso o modelo `Room` fica mais simples (`kdf_salt` e `auth_hash` passam a ser sempre obrigatórios) e só existe um fluxo de entrada.
