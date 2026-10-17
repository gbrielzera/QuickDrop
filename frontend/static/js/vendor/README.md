# Bibliotecas de terceiros

## libsodium (versão 0.8.4, licença ISC)

Criptografia usada no navegador. Arquivos copiados dos pacotes npm
`libsodium-wrappers-sumo` e `libsodium-sumo` (pasta `dist/modules-sumo-esm`).
A versão *sumo* é necessária porque inclui o Argon2id (`crypto_pwhash`).

Única alteração: em `libsodium-wrappers.mjs`, o import `from"libsodium-sumo"` foi trocado por
`from"./libsodium-sumo.mjs"`, para o navegador achar o arquivo sem precisar de bundler.

Para atualizar: baixe os dois pacotes com `npm pack`, copie os arquivos e repita a alteração acima.
