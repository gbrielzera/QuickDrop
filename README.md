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

```powershell
pytest
ruff check .
ruff format .
```
