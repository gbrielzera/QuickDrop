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
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Repare que, para testar com o celular, este comando **não** tem o `--reload`. O `--reload` reinicia o servidor sempre que um arquivo do projeto muda, e a cada reinício o celular perde a conexão e mostra "Sem conexão com o servidor". Use `--reload` só quando estiver programando.

### 2. Descubra o IP do seu PC

```powershell
ipconfig
```

Procure o **"Endereço IPv4"** do adaptador **Wi-Fi** (algo como `192.168.0.15`; o seu será outro). Anote também o **"Gateway Padrão"** (o endereço do roteador, geralmente termina em `.1`): ele ajuda a diagnosticar problemas mais abaixo.

### 3. Libere a porta no Firewall do Windows

Abra o PowerShell **como administrador** (botão direito no PowerShell, "Executar como administrador") e rode **uma vez**:

```powershell
New-NetFirewallRule -DisplayName "QuickDrop (desenvolvimento)" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```

Essa regra só vale para redes marcadas como **Particular**. Confira como o Windows classificou o seu Wi-Fi:

```powershell
Get-NetConnectionProfile
```

Se aparecer `NetworkCategory : Public`, você tem duas opções: mudar a rede para Particular (Configurações > Rede e Internet > Wi-Fi > propriedades da rede > "Particular") ou criar a regra para as duas categorias, trocando `-Profile Private` por `-Profile Private,Public` no comando acima. (Em Wi-Fi de lugares públicos, prefira não deixar a regra ativa: remova-a depois.)

Para remover a regra depois:

```powershell
Remove-NetFirewallRule -DisplayName "QuickDrop (desenvolvimento)"
```

### 4. Abra no celular

No navegador do celular, digite `http://SEU-IP:8000`, usando o IP que você anotou no passo 2 (**não** o `192.168.0.15` dos exemplos). Ou, melhor: crie a sala no PC e **aponte a câmera do celular para o QR Code**. Se o QR Code mostrar `localhost`, abra o QuickDrop no PC pelo IP (`http://SEU-IP:8000`), assim o QR Code já leva o endereço certo.

> Na rede local o endereço é `http://` (sem HTTPS). A criptografia do QuickDrop funciona normalmente assim. A única diferença é o botão "Copiar", que usa um método alternativo.

---

## Instalar como app no celular (opcional)

O QuickDrop pode ser instalado na tela inicial, como um app. O navegador só oferece isso quando o site está em **HTTPS** (ou em `localhost`), então na rede local por `http://192.168...` a opção não aparece; ela passa a funcionar quando o projeto for hospedado na internet. Para ver funcionando no PC: abra http://localhost:8000 no Chrome ou Edge e procure o ícone de instalar na barra de endereço.

## Dicas de uso

- **Cole um print com Ctrl+V** em qualquer lugar da sala: ele é enviado na hora.
- **Ctrl+V com texto** (fora dos campos) guarda um clip.
- **Código:** o campo "Código compartilhado" mantém a indentação (Tab indenta, Shift+Tab tira; Esc e depois Tab sai do campo) e "Blocos de código" guarda trechos para copiar exatamente como foram colados.
- **Ver** mostra uma imagem na própria lista; **Baixar tudo (.zip)** junta todos os arquivos da sala num zip.

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

Para **começar do zero**, pare o servidor (Ctrl + C), apague o arquivo `quickdrop.db` e a pasta `storage` e inicie de novo. As salas expiram sozinhas no tempo escolhido: o servidor apaga o que expirou ao iniciar e a cada 5 minutos (ajustável com `CLEANUP_INTERVAL_MINUTES` no `.env`). Quem estiver na sala vê o aviso "Sala encerrada". O botão **Encerrar sala** apaga tudo na hora.

## Problemas comuns

| Mensagem ou sintoma | O que fazer |
|---|---|
| `python` não é reconhecido | Instale o Python marcando "Add python.exe to PATH" e abra um terminal novo |
| `pydantic ... secret_key Field required` ao iniciar | Falta a `SECRET_KEY` no `backend\.env` (passos 6 e 7) |
| `No module named ...` | O ambiente virtual não está ativo (passo 4) ou faltou o `pip install` (passo 5) |
| `Address already in use` / porta ocupada | Outro programa usa a porta 8000. Use outra: `uvicorn app.main:app --reload --port 8001` |
| O celular não abre o endereço | Veja a seção **"O celular não consegue abrir"** logo abaixo |
| A página abre sem estilo ou sem funcionar | Recarregue com **Ctrl + F5** para limpar o cache |
| Depois de atualizar o projeto, uma tela abre antiga ou um botão novo não aparece | O navegador guardou arquivos de uma versão anterior. Recarregue **sem usar o cache**: Ctrl + F5 no PC; no celular, feche a aba e abra de novo ou limpe os dados do site |
| "Sem conexão com o servidor. Tente de novo." | O servidor parou ou reiniciou. Olhe a janela do terminal onde ele roda: se mostra um erro, ele caiu; se a janela foi fechada, ele parou. Inicie de novo; as páginas abertas reconectam sozinhas em até 30 segundos. Com `--reload`, qualquer arquivo salvo reinicia o servidor |
| "Muitas tentativas. Espere um minuto..." | O limite de tentativas foi atingido (senha errada várias vezes, ou muitas consultas/salas criadas do mesmo aparelho). Espere o tempo indicado; para desenvolvimento, dá para aumentar `RATE_LIMIT_*` no `.env` |
| "Sala não encontrada ou expirada" | A sala expirou ou foi criada em outro banco de dados; crie uma nova |

## O celular não consegue abrir (conexão recusada ou demora)

Faça os testes nesta ordem; o primeiro que falhar mostra o problema.

1. **No próprio PC, abra `http://SEU-IP:8000`** (o IP do passo 2, não `localhost`).
   - Se der **"conexão recusada"**: o servidor não foi iniciado com `--host 0.0.0.0`. Pare (Ctrl + C) e inicie de novo com o comando da seção "Testar com o celular". Com só `uvicorn app.main:app --reload`, ele aceita apenas o próprio PC.
   - Se abrir normalmente: o servidor está certo, e o problema está entre o celular e o PC. Siga para o teste 2.
2. **No celular, abra `http://ENDERECO-DO-ROTEADOR`** (o "Gateway Padrão" do `ipconfig`, ex.: `http://192.168.0.1`).
   - Se **nem o roteador abre**: o celular não está na mesma rede do PC. Desligue os **dados móveis**, confira se é o mesmo nome de Wi-Fi (muitos roteadores têm uma rede 2,4 GHz e outra 5 GHz, ou um repetidor, que ficam separados) e desative VPN ou "DNS privado" no celular.
   - Se o roteador abre: a rede é a mesma. Siga para o teste 3.
3. **Confira o endereço digitado no celular.** Deve ser exatamente `http://SEU-IP:8000`: com `http://` no começo, o IP **do seu PC** e `:8000` no final.
4. **Firewall do Windows**: veja o passo 3 da seção "Testar com o celular", principalmente a classificação da rede (Particular ou Pública).
5. **Isolamento de clientes (AP isolation)**: roteadores, repetidores e Wi-Fi de visitantes têm uma opção que impede os aparelhos de conversarem entre si. Se os testes 1 a 4 estão certos e ainda não abre, procure essa opção no painel do roteador e desative. Uma alternativa rápida para testar: ligue o **hotspot (roteador portátil) do celular**, conecte o PC nele, rode `ipconfig` de novo e use o novo IP.

---

## Resumo rápido (depois da primeira vez)

```powershell
cd QuickDrop\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Depois abra http://localhost:8000.
