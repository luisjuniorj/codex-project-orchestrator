# Avaliar a política de agentes

Há duas categorias diferentes de verificação neste repositório.

## Testes automatizados do instalador

```sh
python -m unittest discover -s tests -v
```

Esses testes usam projetos temporários e verificam arquivos, opções, backups e falhas. Não enviam prompts, não executam modelos e não medem franquia. Seus resultados não comprovam que uma política de agentes é mais econômica ou produz código melhor.

## Casos semânticos para execução futura

`evals/cases.json` contém cinco cenários, cada um com duas formulações do pedido e critérios de avaliação. Eles cobrem uma alteração mecânica extensa, um problema sutil em um arquivo, entregas independentes, falta de acesso a ferramenta e uma restrição explícita de agente único.

Para avaliar a política, prepare um projeto de teste que corresponda ao contexto descrito e execute cada formulação em uma tarefa nova, com o mesmo estado inicial. Registre modelo, effort, agentes criados, verificações e resultado. Não execute as duas formulações em sequência sobre o código já alterado: isso mudaria o problema comparado.

Julgue o comportamento pelo contexto completo e pelas evidências. Não implemente o avaliador procurando palavras específicas na resposta do agente. Um teste útil precisa aceitar formulações equivalentes e distinguir situações parecidas com dependências diferentes.

| Item | O que registrar |
|---|---|
| Configuração | Modo, modelo principal, esforço e versão do Codex. |
| Delegação | Necessidade, escopo, nomes/modelos/efforts dos auxiliares. |
| Correção | Requisito atendido, testes apropriados e defeitos restantes. |
| Retrabalho | Tentativas repetidas e correções necessárias. |
| Uso | Indicador disponível, janela de medição e outras execuções simultâneas. |
| Limitações | Falta de acesso, arredondamentos e fatores que impedem comparação. |

Os critérios não exigem uma resposta textual exata. Em entregas independentes, por exemplo, delegar pode ser útil, mas não é obrigatório se o principal concluir melhor sozinho. Em todos os cenários, uma escolha de Luna deve usar `max`.

Esses casos foram preparados como material de avaliação. Não são resultados observados de execução com modelos. Rode avaliações apenas quando quiser medir esse comportamento e considere o consumo das próprias avaliações.

## Auditoria das decisões

Os quatro arquivos de `templates/agents/` e `templates/policy.md` contêm instruções naturais. Delegação, escolha de escopo, hipótese e necessidade de revisão são decisões do agente. `install.py` usa apenas contratos explícitos de CLI, modelos, caminhos, hashes, TOML e marcadores de bloco para editar arquivos. Ele não recebe pedidos em linguagem natural nem interpreta saídas de modelo.
