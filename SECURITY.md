# Política de segurança

## Versões que recebem correções

Apenas a versão mais recente, na branch `main`. O site de demonstração é atualizado a partir dela.

## Como avisar sobre uma vulnerabilidade

**Não abra um problema (issue) público com detalhes de uma falha.** Use o aviso privado do GitHub:

1. Abra a aba **Security** deste repositório.
2. Clique em **Report a vulnerability** e descreva o que encontrou: o que acontece, como reproduzir e qual o impacto.

Se essa opção não estiver disponível, abra um problema pedindo um contato privado, **sem** descrever a falha.

Você pode esperar uma resposta em alguns dias. Este é um projeto mantido por uma pessoa, sem prazo garantido.

## O que interessa

- Qualquer forma de o servidor, ou outra pessoa sem o link, ler arquivos, textos ou nomes de arquivos de uma sala.
- Entrar numa sala sem o segredo ou a senha, ou fazer um convidado agir como dono (encerrar ou trancar a sala).
- Falhas que apaguem ou corrompam dados de outras salas.
- Formas de esgotar o servidor (disco, memória) com poucos pedidos.
- Problemas na criptografia, nos cookies ou nos cabeçalhos de segurança.

## O que já é conhecido

Estes pontos são limites do desenho, não vulnerabilidades novas:

- Quem esquece a senha escolhida perde o conteúdo; não há recuperação.
- Numa página web, o JavaScript vem do servidor; um servidor invadido poderia entregar código malicioso. O servidor é endurecido e monitorado por causa disso.
- Quem tem o link completo da sala tem acesso a ela até a expiração (o dono pode trancar ou encerrar a sala).

As proteções existentes estão descritas no [Documento de Requisitos](docs/REQUISITOS.md#51-segurança-e-privacidade).
