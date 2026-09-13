# Registro de validação

## Versão 0.3.2

Verificação local em 13 de setembro de 2026, em macOS, com Python 3.14.7 e TOML Kit 0.15.1.

```text
.venv/bin/python -m unittest discover -s tests -v
Ran 45 tests
OK (skipped=1)
```

Foram aprovados 44 testes. O novo teste simula a alteração dos bits de modo após cada escrita no Windows e confirma que a segunda instalação não modifica o manifesto. A saída capturada da CLI também foi decodificada como UTF-8.

O [workflow 34771896187](https://github.com/luisjuniorj/codex-project-orchestrator/actions/runs/34771896187) passou em Linux com Python 3.11, macOS com Python 3.14 e Windows com Python 3.14. A execução anterior falhava somente nos dois jobs Windows por codificação da saída capturada, projeção instável das permissões no manifesto e conversão involuntária de quebras de linha no teste do formatador.

`git diff --check`, compilação dos arquivos Python e validação de `evals/cases.json` passaram. Nenhuma avaliação com modelos foi executada.

## Versão 0.3.1

Verificação local em 13 de setembro de 2026, em macOS, com Python 3.14.7 e TOML Kit 0.15.1.

```text
.venv/bin/python -m unittest discover -s tests -v
Ran 44 tests
OK (skipped=1)
```

Foram aprovados 43 testes. O teste adicional reproduz o espaçamento inserido por um formatador Markdown dentro dos marcadores da política, confirma que a atualização o aceita e verifica a configuração final. Outras divergências continuam cobertas pelos testes conservadores existentes.

`git diff --check` passou. Nenhuma avaliação com modelos foi executada; a suíte usa projetos temporários descartáveis.

## Versão 0.3.0

Verificação local em 13 de setembro de 2026, em macOS, com Python 3.14.7 e TOML Kit 0.15.1.

```text
.venv/bin/python -m unittest discover -s tests -v
Ran 43 tests
OK (skipped=1)
```

Foram aprovados 42 testes. O teste de junction nativa do Windows foi ignorado por exigir Windows. A suíte verifica a configuração única com Sol `max`, papéis Luna `max`, Astra `max` e teto de oito auxiliares simultâneos além do principal.

As novas verificações cobrem a remoção da opção `--mode` sem escrita parcial, a atualização de uma instalação 0.2.0 do teto dois para oito e a atualização e restauração de um estado legado `economy`. Os backups originais permanecem preservados.

Os critérios de paralelismo continuam em instruções naturais: o agente distingue frentes independentes, dependências e conflitos de escrita. O instalador apenas aplica o valor numérico documentado. Os 14 casos semânticos não foram executados com modelos e não comprovam economia ou qualidade.

`git diff --check` passou. Nenhuma avaliação com modelos foi executada; a suíte usa projetos temporários descartáveis.

## Versão 0.2.0

Verificação local em 13 de setembro de 2026, em macOS, com Python 3.14.7 e TOML Kit 0.15.1.

```text
.venv/bin/python -m unittest discover -s tests -v
Ran 41 tests
OK (skipped=1)
```

Foram aprovados 40 testes. O teste de junction nativa do Windows foi ignorado por exigir Windows. A suíte verifica o fluxo instalado com Sol `max`, três papéis Luna `max` e Astra `max`, além dos contratos de instalação e recuperação existentes.

As novas verificações cobrem atualização de uma instalação com os modelos da 0.1.0, prévia sem escrita, preservação dos backups originais, reinstalação idempotente e restauração após atualizar. Também verificam que alterações locais no avaliador antigo impedem a atualização e que `status` mostra a configuração instalada, sem confundi-la com os novos padrões nem inventar um modelo quando há divergência no arquivo.

Foram examinados `install.py`, `templates/policy.md` e os templates de agentes. A busca por padrões de interpretação determinística de linguagem não encontrou roteamento semântico por strings. As comparações do instalador tratam contratos de CLI, versões, modelos, caminhos, hashes, marcadores e configuração TOML; os critérios de avaliação permanecem nas instruções naturais do agente.

`evals/cases.json` foi validado como JSON e contém 14 cenários com 28 formulações de pedidos, incluindo paráfrases, negações, frases citadas, planos e reavaliações. Esses cenários não foram executados com modelos. Os testes automatizados não comprovam a qualidade das decisões semânticas nem economia de franquia.

`git diff --check` passou. Nenhuma avaliação com modelos ou instalação em projeto real foi executada nesta validação; a suíte usa projetos temporários descartáveis.

## Versão 0.1.0

Verificação local em 10 de setembro de 2026, em macOS, com Python 3.14.7 e TOML Kit 0.15.1.

```text
python -m unittest discover -s tests -v
Ran 37 tests
OK (skipped=1)
```

Foram aprovados 36 testes. Um teste de junction nativa do Windows foi ignorado por exigir Windows. A proteção por atributos de reparse point também possui um teste simulado que passou neste ambiente.

A suíte inclui:

- Instalação e desinstalação completas pela CLI.
- Isolamento entre projetos e ausência de alterações na configuração pessoal simulada.
- Modos, Luna `max` e limite de auxiliares.
- Preservação de opções TOML, comentários, instruções e arquivos não gerenciados.
- Prévia sem escrita, idempotência e restauração dos arquivos anteriores.
- Colisões, divergências, backups inválidos, links e metadados com caminhos impróprios.
- Rollback de falhas simuladas e preservação dos backups quando uma edição concorrente impede a restauração completa.

A matriz inicial de CI foi configurada para Linux, macOS e Windows, com Python 3.11 e 3.14. Os resultados por plataforma estão no [GitHub Actions](https://github.com/luisjuniorj/codex-project-orchestrator/actions).

Não foram executadas avaliações de qualidade de modelos, medições da franquia ou instalações em projetos reais do usuário. Os testes criam projetos temporários descartáveis.
