# Changelog

## 0.2.0 — 2026-09-13

- Sol `max` como principal do modo `orchestration`; Luna `max` em leitura, investigação e implementação; Astra `max` na avaliação profunda.
- Avaliação de planos antes da execução, implementações consolidadas grandes ou de alto impacto e solicitações diretas de avaliação aprofundada.
- Critérios interpretados pelo agente, incluindo pedidos equivalentes, negações e frases citadas, sem roteamento por palavras-chave.
- Separação entre coordenação, execução e avaliação; correções e reavaliações delimitadas, com continuidade nas etapas já autorizadas.
- Atualização compatível de instalações intactas da 0.1.0, preservando nomes de agentes, formato de estado e backups originais.
- `status` mostra a versão instalada e lê o principal da configuração em disco, sem confundir instalações antigas com novos padrões.
- Testes de atualização e estado, documentação do fluxo e novos casos semânticos para avaliação futura.

## 0.1.0

- Instalação local por projeto com modos `orchestration`, `everyday` e `economy`.
- Quatro agentes opcionais: explorer, worker, investigator e reviewer.
- Luna sempre em `max`, com limite de dois auxiliares simultâneos.
- Mesclagem de TOML com preservação de comentários e opções não controladas.
- Prévia, verificação de estado, backups, reinstalação idempotente e desinstalação conservadora.
- Proteção contra colisões, divergências, caminhos redirecionados e operações simultâneas do instalador.
- Testes automatizados do instalador e casos separados para avaliação semântica futura.
- Documentação em português, README em inglês e diagramas.

Os testes de arquivos não constituem benchmark de modelos nem comprovação de economia de uso.
