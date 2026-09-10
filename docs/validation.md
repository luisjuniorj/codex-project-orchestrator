# Registro de validação da versão 0.1.0

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
