# QuickDrop

Transferência de arquivos e textos entre dispositivos em tempo real, com criptografia de ponta a ponta.

- Planejamento completo: [PLANEJAMENTO.md](PLANEJAMENTO.md)
- **Visão do produto, com diagramas: [docs/VISAO.md](docs/VISAO.md)**
- **Requisitos funcionais e não funcionais: [docs/REQUISITOS.md](docs/REQUISITOS.md)**
- Regras do projeto: [CLAUDE.md](CLAUDE.md)
- Sistema visual: [DESIGN.md](DESIGN.md) e [PRODUCT.md](PRODUCT.md)
- **Como rodar no seu computador, passo a passo: [COMO-RODAR.md](COMO-RODAR.md)**
- **Como colocar na internet (grátis): [DEPLOY.md](DEPLOY.md)**

## Estrutura

```
backend/    Python / FastAPI (API, WebSocket, banco, armazenamento, testes)
frontend/   HTML (Jinja2), CSS e JavaScript (inclui a criptografia)
```

## Resumo

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Abra http://localhost:8000. Na primeira vez, siga o [COMO-RODAR.md](COMO-RODAR.md) (ambiente virtual, `.env` com `SECRET_KEY`, uso pelo celular na rede local, testes e problemas comuns).
