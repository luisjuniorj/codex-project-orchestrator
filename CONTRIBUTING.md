# Como contribuir

Use Python 3.11 ou superior e instale a dependência no ambiente virtual da cópia local do repositório.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Mudanças no instalador precisam preservar estes contratos:

- Escritas limitadas ao projeto explicitamente informado.
- Nenhuma alteração de configuração pessoal, autenticação ou permissões do Codex.
- Uma única configuração: Sol `max` coordena, Luna `max` executa e Astra `max` avalia planos, entregas grandes ou de alto impacto e pedidos diretos de avaliação aprofundada.
- Luna sempre em `max` nos papéis fornecidos, com teto de oito auxiliares simultâneos além do principal e paralelismo somente entre frentes independentes.
- Integração pelo Sol e verificação pelo executor sem duplicar a avaliação profunda do Astra; reavaliações concentradas nos achados e efeitos das correções.
- TOML existente preservado nas opções não controladas e nos comentários.
- Prévia sem escrita, reinstalação idempotente e backups anteriores à primeira instalação.
- Compatibilidade de consulta, atualização e restauração para estados antigos `orchestration`, `everyday` e `economy`, sem reexpor os modos removidos na CLI.
- Recusa de sobrescrever edições posteriores, caminhos redirecionados e colisões de agentes.
- Falhas normais de escrita com rollback das alterações já realizadas quando ainda for seguro restaurá-las.

Inclua testes de comportamento para mudanças que afetem instalação ou recuperação. Os testes devem trabalhar em pastas temporárias e não chamar modelos, serviços externos ou configurações reais do usuário.

Decisões sobre intenção, delegação, escopo e revisão pertencem ao agente. Não acrescente roteamento por palavras-chave ou interpretação de respostas por regex. Comparações de nomes de modelos, flags, hashes, caminhos e marcadores de blocos são contratos de configuração, não classificação de linguagem natural.

Para mudar prompts ou políticas, atualize os casos em `evals/cases.json` e explique o efeito esperado. Separe testes estáticos e de arquivos de avaliações reais com modelos. Não apresente casos não executados como resultados observados.

Mantenha o README, o guia de instalação, a versão do instalador e o changelog coerentes. Se mudar o formato do manifesto ou os arquivos gerenciados, implemente e teste a migração ou declare claramente a incompatibilidade.

Ao abrir um PR, descreva o comportamento anterior, o comportamento resultante e a validação realizada. Relatos de bugs devem incluir sistema, Python, comando utilizado e passos de reprodução, sem credenciais ou conteúdo privado dos backups.
