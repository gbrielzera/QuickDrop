# QuickDrop

Transferência de arquivos e textos entre dispositivos em tempo real, com criptografia de ponta a ponta.

- Planejamento completo: [PLANEJAMENTO.md](PLANEJAMENTO.md)
- Regras do projeto: [CLAUDE.md](CLAUDE.md)

## Estrutura

```
backend/    Python / FastAPI
frontend/   HTML (Jinja2), CSS e JavaScript
```

## Como rodar (Windows / PowerShell)

Todos os comandos são executados dentro da pasta `backend/`:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```

Abra o arquivo `backend/.env` e troque o valor de `SECRET_KEY` (o app não inicia sem uma chave de verdade). Para gerar uma:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Depois, ainda em `backend/`:

```powershell
uvicorn app.main:app --reload
```

Abra http://localhost:8000 (documentação da API em http://localhost:8000/docs).

### Acessar pelo celular na rede local

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

No celular, abra `http://IP-DO-PC:8000` (veja o IP com `ipconfig`). Se não abrir, libere a porta 8000
no Firewall do Windows para redes privadas.

## Testes e lint

Backend (dentro de `backend/`):

```powershell
pytest
ruff check .
ruff format .
```

Frontend, criptografia (dentro de `frontend/`, precisa do Node 20 ou mais novo):

```powershell
npm test
```

Com `DEBUG=true` no `backend/.env`, a página http://localhost:8000/dev/crypto testa a criptografia no navegador.
