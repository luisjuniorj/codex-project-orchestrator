# Registro de validação

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

A matriz de CI está configurada para Linux, macOS e Windows, com Python 3.11 e 3.14. Os resultados por plataforma estão no [GitHub Actions](https://github.com/luisjuniorj/codex-project-orchestrator/actions).

Não foram executadas avaliações de qualidade de modelos, medições da franquia ou instalações em projetos reais do usuário. Os testes criam projetos temporários descartáveis.
