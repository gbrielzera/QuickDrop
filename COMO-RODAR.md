# Como rodar o QuickDrop no seu computador

Passo a passo para colocar o projeto no ar localmente, no Windows (PowerShell). Leva uns 5 minutos.

## O que você precisa ter instalado

| Programa | Versão | Para quê | Como conferir |
|---|---|---|---|
| **Python** | 3.12 ou mais novo (testado na 3.14) | Rodar o servidor | `python --version` |
| **Git** | qualquer | Baixar o projeto | `git --version` |
| **Node.js** | 20 ou mais novo | **Só** para rodar os testes do frontend (opcional) | `node --version` |

Se o comando `python` não for reconhecido, instale em https://www.python.org/downloads/ e marque a opção **"Add python.exe to PATH"** durante a instalação.

## Passo a passo

### 1. Baixe o projeto

```powershell
git clone https://github.com/gbrielzera/QuickDrop.git
cd QuickDrop
```

Se você já tem a pasta, basta entrar nela.

### 2. Entre na pasta do backend

Todos os comandos seguintes são executados dentro de `backend`:

```powershell
cd backend
```

### 3. Crie o ambiente virtual do Python

Ele guarda as bibliotecas do projeto separadas do resto do computador. Só precisa ser criado uma vez:

```powershell
python -m venv .venv
```

### 4. Ative o ambiente virtual

```powershell
.venv\Scripts\Activate.ps1
```

Quando der certo, o começo da linha do terminal passa a mostrar `(.venv)`.

> Se aparecer um erro dizendo que a execução de scripts está desabilitada, rode este comando e tente de novo. Ele vale só para esta janela do terminal:
>
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

**Toda vez que abrir um terminal novo**, repita este passo 4 antes de rodar o servidor.

### 5. Instale as bibliotecas

```powershell
pip install -r requirements-dev.txt
```

(Esse arquivo inclui as ferramentas de teste. Para só rodar, `requirements.txt` basta.)

### 6. Crie o arquivo de configuração

```powershell
copy .env.example .env
```

### 7. Gere a chave secreta

O servidor **não inicia** sem uma `SECRET_KEY` de verdade: ela assina os cookies das salas. Gere uma com:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie o texto que apareceu. Abra o arquivo `backend\.env` num editor de texto, ache a linha `SECRET_KEY=troque-por-um-valor-aleatorio-longo` e troque o valor pelo que você copiou:

```text
SECRET_KEY=cole-aqui-o-texto-gerado
```

Salve o arquivo. (O `.env` nunca vai para o GitHub: ele está no `.gitignore`.)

### 8. Inicie o servidor

```powershell
uvicorn app.main:app --reload
```

Quando aparecer `Uvicorn running on http://127.0.0.1:8000`, está no ar. O `--reload` reinicia o servidor sozinho quando você edita um arquivo.

### 9. Abra no navegador

http://localhost:8000

Pronto! Crie uma sala e experimente. Para ver o tempo real sem celular, abra o link da sala numa segunda aba (ou numa janela anônima): arquivos enviados ou apagados numa aba aparecem na outra na hora, e o diagrama mostra "Conectado". Para ver a documentação da API: http://localhost:8000/docs

Para parar o servidor, volte ao terminal e aperte **Ctrl + C**.

---

## Testar com o celular (mesma rede Wi-Fi)

O jeito mais útil de experimentar o QuickDrop: PC e celular conectados ao **mesmo Wi-Fi**.

### 1. Inicie o servidor aceitando outros aparelhos

No lugar do passo 8:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Descubra o IP do seu PC

```powershell
ipconfig
```

Procure o **"Endereço IPv4"** do seu Wi-Fi (algo como `192.168.0.15`).

### 3. Libere a porta no Firewall do Windows

Abra o PowerShell **como administrador** (botão direito no PowerShell, "Executar como administrador") e rode **uma vez**:

```powershell
New-NetFirewallRule -DisplayName "QuickDrop (desenvolvimento)" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```

Se o Windows perguntar, deixe a rede do Wi-Fi como **Particular** (não "Pública"). Para remover a regra depois:

```powershell
Remove-NetFirewallRule -DisplayName "QuickDrop (desenvolvimento)"
```

### 4. Abra no celular

No navegador do celular, digite `http://192.168.0.15:8000` (troque pelo seu IP). Ou, melhor: crie a sala no PC e **aponte a câmera do celular para o QR Code**. Se o QR Code mostrar `localhost`, abra o QuickDrop no PC pelo IP (`http://192.168.0.15:8000`), assim o QR Code já leva o endereço certo.

> Na rede local o endereço é `http://` (sem HTTPS). A criptografia do QuickDrop funciona normalmente assim. A única diferença é o botão "Copiar", que usa um método alternativo.

---

## Rodar os testes

Com o ambiente virtual ativado, dentro de `backend`:

```powershell
pytest                 # testes do servidor
ruff check .           # confere o estilo do código
```

Testes do frontend (criptografia e funções do navegador). Precisa do Node.js; rode dentro da pasta `frontend`:

```powershell
cd ..\frontend
npm test
```

## Página de teste da criptografia (opcional)

No `backend\.env`, deixe `DEBUG=true` e abra http://localhost:8000/dev/crypto. Ela mede quanto tempo a derivação de chaves leva no seu aparelho. Abra pelo celular também.

## Onde ficam os dados

| O quê | Onde |
|---|---|
| Salas e lista de arquivos | `backend\quickdrop.db` |
| Arquivos enviados (criptografados) | `backend\storage\` |

Para **começar do zero**, pare o servidor (Ctrl + C), apague o arquivo `quickdrop.db` e a pasta `storage` e inicie de novo. As salas expiram sozinhas no tempo escolhido, mas a limpeza automática dos arquivos antigos do disco só chega numa fase futura do projeto.

## Problemas comuns

| Mensagem ou sintoma | O que fazer |
|---|---|
| `python` não é reconhecido | Instale o Python marcando "Add python.exe to PATH" e abra um terminal novo |
| `pydantic ... secret_key Field required` ao iniciar | Falta a `SECRET_KEY` no `backend\.env` (passos 6 e 7) |
| `No module named ...` | O ambiente virtual não está ativo (passo 4) ou faltou o `pip install` (passo 5) |
| `Address already in use` / porta ocupada | Outro programa usa a porta 8000. Use outra: `uvicorn app.main:app --reload --port 8001` |
| O celular não abre o endereço | Confira: mesmo Wi-Fi, servidor iniciado com `--host 0.0.0.0`, regra do Firewall criada, e que a rede não é "Pública" nem de visitantes (essas redes isolam os aparelhos entre si) |
| A página abre sem estilo ou sem funcionar | Recarregue com **Ctrl + F5** para limpar o cache |
| "Sala não encontrada ou expirada" | A sala expirou ou foi criada em outro banco de dados; crie uma nova |

## Resumo rápido (depois da primeira vez)

```powershell
cd QuickDrop\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Depois abra http://localhost:8000.
