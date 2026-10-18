# Colocar o QuickDrop na internet (grátis)

Guia passo a passo para publicar o QuickDrop numa máquina virtual **grátis da Oracle Cloud**, com HTTPS e um endereço gratuito do DuckDNS. Reserve umas 2 horas na primeira vez.

> O motivo da escolha (e das outras opções descartadas) está em `PLANEJAMENTO.md`, seção 14.1.

## Visão geral

```
Internet ──► Caddy (HTTPS, portas 80/443) ──► app QuickDrop (porta 8000, só dentro do Docker)
                                                   │
                                          volume "quickdrop-data" (banco + arquivos)
```

Tudo roda em dois contêineres Docker, definidos em `docker-compose.yml`.

## Antes de começar

- Uma conta no **GitHub** (já tem) e o código do projeto enviado para lá (`git push`).
- Um **cartão de crédito** para a Oracle confirmar sua identidade. No plano "Always Free" **não há cobrança**; só não ative nada fora da lista de recursos grátis.
- Um e-mail que você acessa.

## Passo 1: criar a conta na Oracle Cloud

1. Acesse <https://www.oracle.com/br/cloud/free/> e clique em **Começar gratuitamente**.
2. Preencha os dados. Em **Região de origem (Home region)** escolha **Brazil East (São Paulo)** ou **Brazil Southeast (Vinhedo)**. **Essa escolha não pode ser trocada depois**, e os recursos grátis só existem nela.
3. Confirme o cartão (aparece uma cobrança pequena que é devolvida) e espere o e-mail de conta pronta.

## Passo 2: criar a máquina virtual

1. No painel da Oracle: **Menu ☰ → Compute → Instances → Create instance**.
2. **Name**: `quickdrop`.
3. **Image and shape → Edit**:
   - **Image**: Ubuntu 24.04 (Canonical Ubuntu, a versão `aarch64`).
   - **Shape**: *Ampere* → `VM.Standard.A1.Flex` com **1 OCPU e 6 GB** de memória (sobra de folga; o limite grátis é 2 OCPU e 12 GB).
4. **Networking**: deixe a rede padrão e confirme que **Assign a public IPv4 address** está marcado.
5. **Add SSH keys**: escolha **Generate a key pair for me** e clique em **Save private key** (baixa um arquivo `.key`). **Guarde esse arquivo**: sem ele você não entra na máquina.
6. **Boot volume**: marque *Specify a custom boot volume size* e use **50 GB**.
7. Clique em **Create**. Se aparecer **"Out of capacity"**, a região está sem máquinas ARM no momento: tente de novo mais tarde (de madrugada costuma funcionar) ou use o shape grátis `VM.Standard.E2.1.Micro` (1 GB de memória, também serve; nesse caso escolha a imagem Ubuntu `x86_64`).
8. Quando o estado ficar **Running**, copie o **Public IP address**.

## Passo 3: abrir as portas 80 e 443 (em dois lugares!)

**Na Oracle** (primeira porta):

1. Na página da máquina, clique na **Subnet** → na **Security List** padrão → **Add Ingress Rules**.
2. Source CIDR `0.0.0.0/0`, IP Protocol **TCP**, Destination Port Range `80,443`. Adicione.

**Dentro do Ubuntu** (segunda porta) você faz no passo 5, depois de entrar na máquina. Esquecer uma das duas é o erro mais comum ("o site não abre").

## Passo 4: criar o endereço no DuckDNS

1. Acesse <https://www.duckdns.org> e entre com sua conta Google ou GitHub.
2. Em **domains**, digite um nome (ex.: `quickdrop-gabriel`) e clique em **add domain**.
3. No campo **current ip**, cole o IP público da máquina (passo 2) e clique em **update ip**.

Seu endereço será `quickdrop-gabriel.duckdns.org`.

## Passo 5: entrar na máquina e instalar o Docker

No PowerShell do seu PC (troque o caminho do arquivo e o IP):

```powershell
icacls "C:\caminho\ssh-key.key" /inheritance:r /grant:r "$($env:USERNAME):R"
ssh -i "C:\caminho\ssh-key.key" ubuntu@IP-DA-MAQUINA
```

(O `icacls` só ajusta a permissão da chave; sem ele o Windows reclama que ela está "desprotegida".)

Já dentro da máquina:

```bash
# 1) Liberar as portas no firewall do Ubuntu (a imagem da Oracle bloqueia tudo por padrão)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p udp --dport 443 -j ACCEPT
sudo apt-get update && sudo apt-get install -y iptables-persistent   # responda "Yes" nas duas perguntas
sudo netfilter-persistent save

# 2) Instalar o Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit
```

Entre de novo com o `ssh` (para o grupo `docker` valer).

## Passo 6: baixar e configurar o QuickDrop

```bash
git clone https://github.com/gbrielzera/QuickDrop.git
cd QuickDrop
cp .env.production.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # copie o resultado
nano .env
```

No `nano`, preencha:

- `DOMAIN`: seu endereço do DuckDNS (sem `https://`).
- `SECRET_KEY`: o valor gerado acima.
- `CONTACT_EMAIL`: seu e-mail para denúncias (opcional).

Salve com **Ctrl+O, Enter** e saia com **Ctrl+X**.

## Passo 7: ligar

```bash
docker compose up -d --build
docker compose ps          # os dois serviços devem estar "running"
docker compose logs -f     # acompanhe; Ctrl+C sai (não desliga nada)
```

Na primeira vez o Caddy demora alguns segundos para obter o certificado HTTPS. Abra `https://SEU-ENDERECO.duckdns.org` no navegador: deve aparecer o QuickDrop com o cadeado.

## Passo 8: conferir

- [ ] Cadeado do HTTPS no PC **e no celular usando 4G** (fora do seu Wi-Fi).
- [ ] Criar uma sala no PC, entrar pelo QR Code no celular.
- [ ] Enviar um arquivo grande (perto de 100 MB) e baixar no outro aparelho.
- [ ] Texto e código aparecendo ao vivo nos dois lados.
- [ ] Apagar a tela do celular por 1 minuto, acender de novo: a sala deve reconectar.
- [ ] Tempo de entrada numa sala com senha (a derivação Argon2id) abaixo de ~1 s no celular.
- [ ] `https://SEU-ENDERECO.duckdns.org/sobre` abre e mostra seu e-mail de contato.

## Atualizar depois

No servidor, dentro da pasta `QuickDrop`:

```bash
git pull
docker compose up -d --build
```

Os arquivos e o banco ficam no volume e não se perdem. As salas ativas continuam (os aparelhos reconectam sozinhos).

## Comandos úteis

| Para quê | Comando |
|---|---|
| Ver os registros do app | `docker compose logs -f app` |
| Reiniciar | `docker compose restart` |
| Desligar | `docker compose down` (os dados ficam) |
| Quanto disco os arquivos usam | `docker system df -v` |
| Apagar **tudo**, inclusive os dados | `docker compose down -v` |

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| O site não abre (fica carregando) | Porta fechada em um dos dois lugares do passo 3/5. Confira a Security List **e** o `iptables` |
| Erro de certificado ou "conexão não é segura" | O DuckDNS ainda aponta para outro IP, ou a porta 80 está fechada (o Let's Encrypt usa a 80). Veja `docker compose logs caddy` |
| "Out of capacity" ao criar a máquina | Sem ARM livre na região agora: tente de novo mais tarde ou use a máquina AMD Micro |
| "O servidor está cheio agora" | Passou do `MAX_TOTAL_STORAGE_MB` ou `MAX_ACTIVE_ROOMS` do `.env`. Aumente (e rode `docker compose up -d`) ou espere salas expirarem |
| Todo mundo bloqueado ao mesmo tempo ("Muitas tentativas") | O app não está enxergando o IP real. Confirme que usa o `docker-compose.yml` do projeto (ele liga o `--proxy-headers`) |
| A máquina sumiu | A Oracle pode recuperar máquinas grátis paradas por muito tempo. Refaça os passos 2 a 7 (cerca de 20 minutos) |

## Segurança: o que já está feito e o que é com você

Já feito pelo projeto: HTTPS obrigatório (cookie `Secure` e HSTS ligados), cabeçalhos de segurança, limite de tentativas por IP real, conteúdo sempre criptografado no navegador, app sem privilégios de administrador dentro do contêiner e porta 8000 sem acesso direto da internet.

Com você: manter o `.env` e a chave `.key` só com você; não abrir outras portas; rodar `sudo apt-get update && sudo apt-get upgrade` de vez em quando (o Ubuntu da Oracle também instala atualizações de segurança sozinho).
