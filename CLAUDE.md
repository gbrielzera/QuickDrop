# Regras do projeto QuickDrop

O planejamento completo está em `docs/PLANEJAMENTO.md`. Siga estas regras em todo o código.

## 1. Clean code, sempre

O código deve ser simples e legível o bastante para que uma pessoa **sem muita experiência** consiga entendê-lo.

- **Nomes claros e completos**: `room_code`, `expires_at`, `encrypt_file`. Evite abreviações (`rc`, `exp`, `enc_f`).
- **Funções pequenas e com uma única responsabilidade.** Se precisar de "e" para descrever o que a função faz, divida-a.
- **Sem "mágica"**: prefira o jeito direto e explícito ao jeito esperto. Evite recursos avançados ou obscuros da linguagem quando uma solução comum resolve.
- **Retorno antecipado** (`if erro: return ...`) em vez de `if` aninhados.
- **Sem números mágicos**: valores fixos viram constantes com nome ou configurações (`MAX_FILE_SIZE_MB`).
- **Comentários explicam o *porquê*, não o *quê*.** O código deve se explicar sozinho; comente decisões não óbvias (especialmente de segurança e criptografia).
- **Docstring curta** nas funções públicas, dizendo o que fazem.
- **Type hints** em todas as funções Python.
- **Nada de código morto** nem arquivos "para o futuro": cada arquivo é criado na fase em que é usado.
- Nomes de código em **inglês**; textos para o usuário, comentários e documentação em **português**.
- Formatação e lint com `ruff` (rodar `ruff check .` e `ruff format .` em `backend/`).

## 2. Todos os tipos de arquivo são permitidos

Não existe lista de extensões permitidas ou bloqueadas: PDF, DOCX, XML, TXT, executáveis, extensões raras, tudo é aceito.
A segurança não depende do tipo do arquivo:

- O conteúdo chega ao servidor **criptografado**; o servidor nem sabe o tipo real.
- Arquivos são salvos no disco com nome **UUID**, nunca com o nome original.
- Downloads sempre com `Content-Disposition: attachment` e `X-Content-Type-Options: nosniff`.
- Pré-visualização no navegador só para tipos seguros (imagens comuns, texto puro). **Nunca** renderizar HTML ou SVG enviado pelo usuário.

Os únicos limites são de **tamanho**: 100 MB por arquivo e 500 MB por sala.

## 3. Backend e frontend em pastas separadas

```
backend/    → Python / FastAPI (API, WebSocket, banco, armazenamento, testes)
frontend/   → templates Jinja2, CSS, JavaScript (incluindo a criptografia)
```

- O backend **serve** o frontend (mesmo servidor, mesma origem: evita CORS e simplifica os cookies), mas o código de cada um fica na sua pasta.
- Nada de HTML, CSS ou JS dentro de `backend/`; nada de Python dentro de `frontend/`.

## Comandos

Rodar a partir da pasta `backend/`:

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
pytest
ruff check .
ruff format .
```

Testes da criptografia, a partir da pasta `frontend/`:

```powershell
npm test
```
