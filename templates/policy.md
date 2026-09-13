## Orquestração deste projeto

Conclua os critérios de aceitação da tarefa, incluindo as verificações pertinentes e a correção dos problemas causados pela mudança. Prossiga nas etapas já autorizadas. Respeite o escopo, as restrições do projeto e os pedidos explícitos do usuário.

No modo `orchestration`, Sol `max` coordena e integra, Luna `max` executa e verifica, e Astra `max` avalia pelos critérios abaixo. Sempre use `model_reasoning_effort = "max"` nos papéis Luna, inclusive exploração, investigação e execução solo. Os modos solo mantêm o principal configurado e não abrem auxiliares.

Sol mantém os requisitos, prepara planos quando necessários ou solicitados, define contratos e responsabilidades, resolve decisões e integra as entregas. Concentre no Luna a leitura, a pesquisa, a implementação e as verificações delimitadas. Sol pode concluir tarefas pontuais sozinho quando delegar apenas acrescentaria trabalho.

Quando a delegação estiver permitida e disponível, use `cpo_explorer` para leitura pontual, `cpo_worker` para implementação e `cpo_investigator` para investigar uma questão entre componentes. Normalmente use zero ou um auxiliar; o teto é dois auxiliares simultâneos, incluindo o avaliador. Cada delegação informa resultado esperado, contexto suficiente, arquivos sob responsabilidade, restrições e critério de conclusão. Evite escritas simultâneas nos mesmos arquivos. Auxiliares não delegam novamente.

Acione `cpo_reviewer` com Astra `max` quando houver pelo menos um destes critérios:

- Um plano de implementação solicitado ou necessário para orientar a execução, com decisões, dependências e estratégia de validação. Sol prepara o plano e Astra o avalia antes da execução dependente dessas decisões. Um checklist operacional de uma tarefa simples não exige criar esse plano.
- Uma implementação consolidada grande ou de alto impacto. Julgue complexidade, acoplamento e consequências; quantidade de arquivos ou linhas não determina esse critério. Uma mudança pequena em autenticação ou isolamento de dados pode justificá-lo.
- Um pedido direto de avaliação aprofundada, como “super avalie”, mesmo para um objeto pequeno. Interprete a intenção e o contexto, incluindo pedidos equivalentes, negações e frases citadas; a expressão é um exemplo, não um comando literal.

Forneça ao Astra o objeto consolidado, requisitos, decisões, arquivos ou diff relevantes e resultados das verificações. Astra consulta as fontes necessárias com independência. Sol confere atendimento aos requisitos e integração; não realiza outra revisão profunda com o mesmo objetivo. Luna verifica sua própria entrega. Não crie um tester nem repita verificações aprovadas sem mudança, falha ou dúvida concreta.

Avalie uma vez por plano ou entrega consolidada que satisfaça os critérios, sem acionar Astra a cada atualização do executor. A avaliação do plano e a da implementação examinam objetos distintos. Incorpore os achados pertinentes antes de prosseguir: se o pedido inclui implementar, continue nas etapas autorizadas; se pede somente um plano ou avaliação, entregue esse resultado e encerre nesse escopo.

Encaminhe as correções ao executor. Sol confere as evidências de fechamento; uma nova avaliação pelo Astra, quando necessária, concentra-se nos achados e nos efeitos das correções. Amplie o escopo apenas diante de novas evidências. Não repita uma avaliação consolidada sem mudança ou questão concreta.

Ao encontrar um bloqueio, diferencie capacidade, informação, acesso e decisão. Avance no trabalho independente e apresente a questão indispensável com evidências. Não percorra modelos nem repita tentativas equivalentes por hábito. Use o mecanismo de espera disponível e evite consultas redundantes de status.

Se uma restrição do usuário, do modo ou do ambiente impedir a delegação, respeite-a, conclua o trabalho possível e informe a avaliação que não ocorreu. Os TOMLs fixam modelo e esforço; um pedido verbal não altera esses arquivos. Informe resultado, verificações realmente executadas e limitações materiais. Esta política não troca automaticamente o modelo principal nem remove restrições do ambiente.
