## Orquestração deste projeto

Conclua corretamente a tarefa com uso proporcional de agentes e ferramentas. Respeite as restrições do projeto e os pedidos explícitos do usuário.

Sempre que usar GPT-5.6 Luna, configure `model_reasoning_effort = "max"`, inclusive em exploração, implementação, execução solo e novos papéis Luna. Essa é a política de esforço escolhida para este projeto. Os demais modelos têm esforço definido por função.

O principal mantém a responsabilidade pelos requisitos, pelas decisões centrais, pela implementação e pela validação final. Trabalhe sozinho quando isso atender bem à tarefa.

Quando as ferramentas de subagentes estiverem habilitadas, delegue seletivamente uma entrega concreta ou uma investigação independente se houver benefício claro para o resultado. Decida pelo significado da tarefa, pelas dependências, pelo contexto necessário e pela possibilidade de verificar a entrega. A quantidade de arquivos não determina a necessidade de delegar.

Normalmente use zero ou um auxiliar; o teto é dois auxiliares simultâneos, incluindo revisores. Use `cpo_explorer` para leitura pontual, `cpo_worker` para implementação delimitada e `cpo_investigator` para uma investigação que exige seguir comportamento entre componentes. Use `cpo_reviewer` quando uma análise independente puder encontrar problemas relevantes que a validação atual não esclarece. Todos esses papéis são opcionais.

Cada delegação deve informar resultado esperado, contexto suficiente, arquivos sob responsabilidade do auxiliar, restrições, critério de conclusão e verificação pertinente. Evite alterações simultâneas nos mesmos arquivos. Auxiliares não devem delegar novamente.

O executor verifica sua própria entrega, cumprindo os checks exigidos pelo projeto. Não crie um tester apenas para repetir comandos. Não repita verificações já aprovadas sem nova alteração, falha ou dúvida concreta. Use o mecanismo de espera disponível e evite consultas redundantes de status.

Ao encontrar um bloqueio, diferencie falta de capacidade, informação, acesso e decisão. Não percorra todos os modelos por hábito nem repita tentativas equivalentes sem nova evidência. Os TOMLs dos agentes fixam modelo e esforço; não presuma que um pedido verbal substitua esses valores.

Informe o resultado, a validação realmente executada e as limitações materiais. Esta política permite delegação seletiva; não instala troca automática de modelo principal e não remove restrições do ambiente.
