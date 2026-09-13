# Instalação por projeto

O instalador grava apenas dentro do destino informado em `--project`. O ambiente virtual Python fica na cópia deste repositório. Não é necessário instalar um plugin, configurar uma chave de API ou alterar arquivos pessoais do Codex.

## Pré-requisitos e preparação

Use Python 3.11 ou superior e um Codex que aceite os agentes personalizados e as opções descritos na documentação atual. Os modelos precisam estar disponíveis para a conta e para o cliente. Não há verificação de acesso a modelos pelo instalador; uma instalação válida em disco não concede acesso a eles.

O projeto deve ser confiável no Codex. O instalador não altera a confiança nem ignora políticas administradas. Instruções globais e arquivos de instruções mais próximos de uma subpasta podem continuar afetando a sessão.

Na raiz deste repositório, em macOS ou Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python install.py --help
```

No PowerShell, sem exigir ativação do ambiente:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe install.py --help
```

O download da dependência acontece nessa preparação. Os comandos `install`, `status` e `uninstall` não fazem chamadas de rede ou de modelo. Para instalação offline, prepare a dependência previamente com os mecanismos usuais de distribuição de pacotes Python.

## Prévia e aplicação

```sh
python install.py install --project "/caminho/do/projeto" --dry-run
python install.py install --project "/caminho/do/projeto"
```

O destino precisa existir. Use a raiz do projeto, não a pasta `.codex` nem uma pasta pessoal. Caminhos com espaços são aceitos; use aspas. Links simbólicos, junctions e arquivos com hard links nos destinos gerenciados são rejeitados para evitar redirecionar alterações para fora do projeto.

A prévia mostra os arquivos a criar ou atualizar. Não imprime o conteúdo de configurações nem cria pastas, backups ou locks.

A aplicação executa estas operações:

1. Lê e valida o TOML existente.
2. Confere colisões com os quatro nomes de agentes `cpo_*`.
3. Identifica `AGENTS.override.md` não vazio ou `AGENTS.md` na raiz.
4. Guarda cópias dos arquivos existentes em `.codex/.project-orchestrator/original/`.
5. Mescla as opções controladas, escreve os agentes e acrescenta um bloco de política delimitado.
6. Registra hashes e permissões dos arquivos para detectar alterações posteriores.

As opções controladas são `model`, `model_reasoning_effort` e estas chaves de `[agents]`: `enabled`, `max_concurrent_threads_per_session`, `default_subagent_model` e `default_subagent_reasoning_effort`. O alias antigo `max_threads` é removido ao definir o limite atual; a cópia anterior é preservada para restauração.

Outras opções e comentários TOML são preservados com TOML Kit. A autenticação, provedores, MCPs, sandbox e permissões não são alterados. Um bloco em `.codex/.gitignore` exclui a pasta de estado e backups do Git.

## Ativar no Codex

Abra uma nova tarefa no projeto confiável. Verifique o modelo principal, o esforço e as instruções carregadas. O esperado é Sol `max` com até oito auxiliares habilitados; os três papéis de execução usam Luna `max` e o avaliador usa Astra `max`.

Faça uma primeira tarefa pequena e, se quiser validar a delegação, peça explicitamente uma leitura delimitada por `cpo_explorer`. Confira os dados da execução disponibilizados pelo cliente, além do TOML. Uma declaração do modelo sobre qual modelo ele é não substitui essa verificação.

O instalador não força Standard nem altera `service_tier`. Se preservar uso for prioridade, confira Fast desligado; na CLI, use `/fast off` e `/fast status`. Modelos e esforços definidos no arquivo do agente personalizado prevalecem sobre valores resolvidos na criação do auxiliar.

## Atualizar

Execute novamente `install`. A instalação precisa estar intacta. O instalador expõe uma única configuração e não aceita `--mode`.

Uma nova versão deste repositório pode atualizar os templates ao executar novamente o instalador, desde que mantenha o formato de estado compatível e os arquivos não tenham sido editados. O backup da primeira instalação permanece. Revise o changelog e use `--dry-run` antes de atualizar.

A versão 0.3.0 atualiza instalações intactas das versões 0.1.0 e 0.2.0 com o mesmo formato de estado e os mesmos quatro nomes de agentes. A atualização aplica Sol `max`, Luna `max`, Astra `max` e eleva o teto de dois para oito auxiliares. Instalações antigas em `everyday` ou `economy` podem ser consultadas, atualizadas e desinstaladas, mas novas instalações não expõem esses modos. O comando `status` mostra a versão e a configuração efetivamente instaladas, sem atribuir os novos valores a um projeto que ainda não foi atualizado.

Se os arquivos gerados forem versionados e clonados em outra máquina, o Codex pode usá-los diretamente. A nova cópia não possui os backups locais da instalação original; o instalador não adota silenciosamente esses arquivos como se os tivesse criado. Use a instalação manual para mantê-los, ou prepare uma instalação registrada após uma remoção revisada dos arquivos da configuração anterior.

## Arquivos modificados e recuperação

Uma alteração posterior em qualquer arquivo gerenciado provoca divergência, mesmo quando é uma edição válida e independente da orquestração. `status` informa o caminho; `install` e `uninstall` recusam sobrescrever. Esse comportamento é conservador e não tenta adivinhar a intenção de uma edição.

Para remover ou atualizar nesse caso:

1. Preserve sua versão atual com Git ou uma cópia local.
2. Compare os arquivos com as cópias em `.codex/.project-orchestrator/original/` e com os templates desta versão.
3. Mescle manualmente as alterações que deseja manter. Para remover a política, retire somente o bloco entre os marcadores `codex-project-orchestrator:begin` e `codex-project-orchestrator:end` do arquivo de instruções.
4. Restaure ou remova apenas as opções e os agentes associados a esta instalação, preservando o restante.
5. Depois de verificar a recuperação, remova o estado local que deixou de representar a instalação.

Não apague os backups antes de concluir a comparação. Para agentes personalizados, uma cópia anterior pode não existir: isso indica que o arquivo foi criado pela instalação.

Falhas normais de escrita acionam rollback das alterações já realizadas, desde que esses arquivos não tenham mudado novamente. Cada substituição de arquivo é atômica, mas a transação completa não é resistente a encerramento forçado do processo, queda de energia ou alterações concorrentes externas. Nessas situações, preserve o estado e os backups e faça a recuperação manual.

Um `install.lock` indica outra execução ou uma interrupção. Confirme que não existe outro instalador trabalhando nesse projeto antes de remover um lock remanescente. Não use a remoção do lock para contornar uma execução ativa.

## Desinstalar uma instalação intacta

```sh
python install.py uninstall --project "/caminho/do/projeto" --dry-run
python install.py uninstall --project "/caminho/do/projeto"
```

Arquivos anteriores são restaurados byte a byte, e arquivos criados pelo instalador são removidos. Arquivos não gerenciados são preservados. Pastas criadas pelo instalador são removidas apenas se estiverem vazias. O comando depende dos metadados e backups locais intactos.

## Instalação manual

Essa opção dispensa Python e o histórico de restauração do instalador. Ela exige mesclagem e revisão manuais.

1. Copie os quatro arquivos de `templates/agents/` para `.codex/agents/` do projeto.
2. Acrescente a política de `templates/policy.md` ao arquivo de instruções local efetivamente carregado.
3. Mescle a configuração abaixo em `.codex/config.toml`, sem duplicar chaves ou tabelas.

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "max"

[agents]
enabled = true
max_concurrent_threads_per_session = 8
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "max"
```

Uma instalação manual não pode ser desfeita pelo comando `uninstall`, pois ele não possui seu estado anterior. Preserve suas próprias cópias ou use o histórico do Git.

## Códigos de saída

| Código | Significado |
|---|---|
| `0` | Operação concluída, prévia válida ou instalação conferida em disco. |
| `1` | `status` não encontrou uma instalação registrada. |
| `2` | Erro de uso, conflito, divergência, backup inválido ou falha de operação. |

Referências: [agentes personalizados](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents), [precedência](https://learn.chatgpt.com/docs/config-file/config-basic#configuration-precedence) e [descoberta de instruções](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
