# Avaliar a política de agentes

Há duas categorias diferentes de verificação neste repositório.

## Testes automatizados do instalador

```sh
python -m unittest discover -s tests -v
```

Esses testes usam projetos temporários e verificam arquivos, opções, backups e falhas. Não enviam prompts, não executam modelos e não medem franquia. Seus resultados não comprovam que uma política de agentes é mais econômica ou produz código melhor.

## Casos semânticos para execução futura

`evals/cases.json` contém quatorze cenários, cada um com duas formulações do pedido e critérios de avaliação. Os cinco cenários iniciais cobrem alteração mecânica extensa, problema sutil, entregas independentes, falta de acesso e restrição de agente único.

Os nove cenários adicionais cobrem planos de implementação, entregas grandes, mudanças pequenas de alto impacto, pedidos diretos de avaliação aprofundada, frases citadas, exclusão explícita do Astra, planejamento seguido de implementação, reavaliação de correções e tarefas simples que dispensam um plano formal.

Para avaliar a política, prepare um projeto de teste que corresponda ao contexto descrito e execute cada formulação em uma tarefa nova, com o mesmo estado inicial. Registre modelo, effort, agentes criados, verificações e resultado. Não execute as duas formulações em sequência sobre o código já alterado: isso mudaria o problema comparado.

Julgue o comportamento pelo contexto completo e pelas evidências. Não implemente o avaliador procurando palavras específicas na resposta do agente. Um teste útil precisa aceitar formulações equivalentes e distinguir situações parecidas com dependências diferentes.

| Item | O que registrar |
|---|---|
| Configuração | Modelo principal, esforço, teto de auxiliares e versão do Codex. |
| Delegação | Necessidade, escopo, nomes/modelos/efforts dos auxiliares. |
| Avaliação pelo Astra | Critério aplicado, objeto e momento da avaliação; continuidade após avaliar o plano quando a implementação já está autorizada. |
| Correção | Requisito atendido, testes apropriados e defeitos restantes. |
| Retrabalho | Tentativas repetidas, correções necessárias, avaliações duplicadas entre Sol e Astra e ampliação justificada de reavaliações. |
| Uso | Indicador disponível, janela de medição e outras execuções simultâneas. |
| Limitações | Falta de acesso, arredondamentos e fatores que impedem comparação. |

Os critérios não exigem uma resposta textual exata. Em entregas independentes, deve-se avaliar paralelismo útil sem criar divisão artificial; há capacidade para até oito auxiliares, excluindo o principal. Sol, Luna e Astra usam `max`. Quando um critério de avaliação estiver presente e a delegação for permitida, o Astra deve ser acionado.

Compare especialmente `explicit_deep_evaluation`, `quoted_trigger_is_not_a_request` e `explicit_review_opt_out`: pedidos equivalentes de avaliação devem acionar o Astra, enquanto uma frase citada ou negada não deve funcionar como comando. `implementation_plan` e `plan_then_implementation` distinguem entregar somente um plano de continuar até concluir uma implementação autorizada. Uma restrição de agente único continua valendo mesmo para um plano que normalmente seria avaliado pelo Astra.

Esses casos foram preparados como material de avaliação. Não são resultados observados de execução com modelos. Rode avaliações apenas quando quiser medir esse comportamento e considere o consumo das próprias avaliações.

## Auditoria das decisões

Os quatro arquivos de `templates/agents/` e `templates/policy.md` contêm instruções naturais. Intenção, delegação, complexidade, escopo, hipótese, momento de avaliação e necessidade de reavaliação são decisões do agente. `install.py` usa apenas contratos explícitos de CLI, versões, modelos, caminhos, hashes, TOML e marcadores de bloco para editar arquivos. Ele não recebe pedidos em linguagem natural nem interpreta saídas de modelo.
