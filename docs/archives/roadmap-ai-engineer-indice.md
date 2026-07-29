# Roadmap AI Engineer — Índice Completo (Júnior · Pleno · Sênior · Staff)


## JÚNIOR — JÚNIOR Uso de AI


**1. Modelos & Inference Básico + Intermediário** *(próprio)*
- 1.1 Comparar modelos por janela de contexto, latência, custo, qualidade, multimodalidade e requisitos de implantação
- 1.2 Configurar parâmetros de inferência como temperature, top-p, max tokens, stop sequences e seed quando disponível
- 1.3 Implementar chamadas a APIs de modelos com autenticação, rate limits, retries, timeouts e tratamento de erros
- 1.4 Estruturar entradas e saídas com JSON schema, function calling, tool use e validação programática
- 1.5 Avaliar respostas de modelos com testes offline, golden datasets, métricas de qualidade e análise de falhas
- 1.6 Otimizar custo e desempenho com batching, caching, streaming, fallback de modelos e roteamento por tarefa

**2. Prompt Engineering & Interaction Básico + Intermediário** *(próprio)*
- 2.1 Escrever prompts estruturados com objetivo, contexto, restrições, formato de saída e critérios de qualidade
- 2.2 Criar instruções reutilizáveis para tarefas de classificação, extração, sumarização, geração e transformação de texto
- 2.3 Aplicar few-shot prompting com exemplos positivos, negativos, contraexemplos e padrões de resposta esperados
- 2.4 Projetar fluxos conversacionais com memória de contexto, coleta incremental de informações e tratamento de ambiguidades
- 2.5 Implementar validação de saídas com rubricas, formatos estruturados, checagem de consistência e retry orientado
- 2.6 Reduzir alucinações com grounding, delimitação de fontes, perguntas de clarificação e verificação de evidências

**3. Desenvolvimento de Software Básico** *(referência → `software-basico`, Software Engineer)*
- 3.1 Sintaxe da linguagem principal
- 3.2 Tipos de dados e estruturas básicas
- 3.3 Controle de fluxo if e loops
- 3.4 Funções e escopo
- 3.5 Estruturas de dados simples array e map
- 3.6 Manipulação de dados map filter reduce
- 3.7 Leitura e escrita básica input output
- 3.8 Debug básico logs e breakpoints
- 3.9 Uso básico de Git clone commit push
- 3.10 Execução de código local

**4. Desenvolvimento de Software Intermediário** *(referência → `software-intermediario`, Software Engineer)*
- 4.1 Programação assíncrona async await promises
- 4.2 Tratamento de erros estruturado
- 4.3 Modularização de código
- 4.4 Organização de projetos em camadas
- 4.5 Integração com APIs REST
- 4.6 Serialização JSON
- 4.7 Testes unitários básicos
- 4.8 Refatoração de código
- 4.9 Gerenciamento de estado
- 4.10 Git avançado branch PR merge

**5. Design de Software Básico** *(referência → `design-software-basico`, Software Engineer)*
- 5.1 Separação de responsabilidades
- 5.2 Organização em camadas controller service repository
- 5.3 Conceito de modularização
- 5.4 Introdução a SOLID
- 5.5 Leitura de código estruturado
- 5.6 Baixo acoplamento e alta coesão conceito

**6. Banco de Dados Básico** *(referência → `banco-dados-basico`, Software Engineer)*
- 6.1 Conceito de banco relacional
- 6.2 CRUD insert select update delete
- 6.3 Estrutura de tabelas
- 6.4 Tipos de dados (SQL)
- 6.5 Queries simples WHERE
- 6.6 Uso básico de ORM

**7. Cloud Fundamentals Básico** *(referência → `cloud-fundamentals-basico`, Software Engineer)*
- 7.1 Conceito de cloud computing
- 7.2 IaaS PaaS SaaS
- 7.3 Deploy de aplicações
- 7.4 Storage object storage
- 7.5 Conceito de região e zona
- 7.6 Custos básicos
- 7.7 Conceito de escalabilidade

**8. DevOps Fundamentals** *(referência → `devops-fundamentals`, Software Engineer)*
- 8.1 Conceito de CI CD
- 8.2 Pipeline básico
- 8.3 Versionamento
- 8.4 Deploy automatizado simples
- 8.5 Integração contínua
- 8.6 Conceito de automação

## PLENO — PLENO Sistemas com AI

_Herda todo o bloco Júnior (por herança; não repetido abaixo)._


**9. Data Engineering & Pipelines Básico + Intermediário** *(próprio)*
- 9.1 Construir pipelines batch e incrementais para ingestão, transformação, validação e carga de dados para IA
- 9.2 Processar dados estruturados e não estruturados com normalização, deduplicação, chunking e enriquecimento
- 9.3 Implementar validações de schema, qualidade, completude, consistência e rastreabilidade em datasets
- 9.4 Orquestrar workflows com dependências, retries, backfills, checkpoints e execução idempotente
- 9.5 Preparar datasets para embeddings, fine-tuning, avaliação, busca semântica e consumo por aplicações de IA
- 9.6 Monitorar pipelines com logs, métricas de volume, latência, falhas, registros rejeitados e freshness

**10. Cloud for AI Básico + Intermediário** *(próprio)*
- 10.1 Provisionar recursos cloud para execução de workloads de IA com compute, storage, rede e permissões
- 10.2 Configurar ambientes para APIs de modelos, bancos vetoriais, filas, funções serverless e serviços gerenciados
- 10.3 Gerenciar secrets, variáveis, credenciais, quotas, rate limits e segregação por ambiente
- 10.4 Implementar armazenamento de datasets, embeddings, prompts, artefatos, logs e resultados de inferência
- 10.5 Configurar deploy de aplicações de IA com autoscaling, balanceamento, cache e observabilidade básica
- 10.6 Monitorar custos, uso de tokens, consumo de compute, storage, chamadas de API e limites operacionais

**11. DevOps for AI Básico + Intermediário** *(próprio)*
- 11.1 Criar pipelines CI/CD para aplicações de IA com testes, lint, validação de prompts, build e deploy
- 11.2 Versionar prompts, datasets, embeddings, configurações de modelos e artefatos de avaliação
- 11.3 Automatizar avaliações offline com golden datasets, regressão de qualidade, critérios de aceitação e bloqueios de release
- 11.4 Configurar observabilidade com logs de prompts, respostas, latência, custo, erros, feedback e traces de execução
- 11.5 Gerenciar ambientes, secrets, quotas, rate limits, fallback de modelos e rollback de versões
- 11.6 Implementar guardrails operacionais com validação de entrada, schema de saída, retries e tratamento de falhas

**12. Memory & Retrieval RAG Básico + Intermediário** *(próprio)*
- 12.1 Implementar pipelines de ingestão para documentos com parsing, limpeza, chunking, metadados e versionamento
- 12.2 Gerar embeddings e indexar conteúdos em bancos vetoriais com filtros, namespaces e estratégias de atualização
- 12.3 Construir fluxos RAG com retrieval, reranking, contexto controlado, citações e composição de resposta
- 12.4 Avaliar qualidade de recuperação com precision, recall, relevância, cobertura, groundedness e análise de falhas
- 12.5 Otimizar chunk size, overlap, top-k, filtros, hybrid search e estratégias de ranking por domínio
- 12.6 Implementar memória conversacional com histórico resumido, contexto persistido, expiração e isolamento por usuário

**13. Agentic Systems Básico + Intermediário** *(próprio)*
- 13.1 Projetar agentes com objetivos, instruções, ferramentas disponíveis, limites de execução e critérios de parada
- 13.2 Implementar tool calling com schemas, validação de argumentos, tratamento de erros e retorno estruturado
- 13.3 Criar fluxos multi-step com planejamento, execução, observação, revisão e controle de estado
- 13.4 Integrar agentes com APIs, bancos de dados, sistemas internos, filas e mecanismos de busca
- 13.5 Aplicar guardrails para permissões, escopo de ferramentas, validação de ações e prevenção de loops
- 13.6 Avaliar agentes com cenários de teste, traces, taxa de sucesso, custo, latência e análise de falhas

**14. Banco de Dados Intermediário** *(referência → `banco-dados-intermediario`, Software Engineer)*
- 14.1 Joins inner left right
- 14.2 Índices
- 14.3 Normalização
- 14.4 Transações
- 14.5 Queries complexas
- 14.6 Paginação
- 14.7 Introdução a NoSQL
- 14.8 Cache básico Redis

**15. Design de Software Intermediário** *(referência → `design-software-intermediario`, Software Engineer)*
- 15.1 SOLID aplicado
- 15.2 Design patterns factory strategy observer
- 15.3 Dependency Injection
- 15.4 Interfaces e contratos
- 15.5 Testabilidade de código
- 15.6 Organização por domínio feature based
- 15.7 Refatoração para melhorar design

## SÊNIOR — SÊNIOR Arquitetura de AI

_Herda todo o bloco Pleno (por herança; não repetido abaixo)._


**16. AI Architecture & Orchestration Básico + Intermediário + Avançado** *(próprio)*
- 16.1 Arquitetar aplicações de IA com camadas de interface, orquestração, modelos, ferramentas, memória, avaliação e observabilidade
- 16.2 Projetar fluxos multi-etapa com roteamento de tarefas, decomposição, validação, fallback e controle de estado
- 16.3 Implementar orquestração de pipelines de IA com filas, workers, eventos, retries, timeouts e execução assíncrona
- 16.4 Definir padrões de integração entre LLMs, APIs internas, bancos vetoriais, sistemas transacionais e ferramentas externas
- 16.5 Criar arquiteturas resilientes com circuit breakers, rate limiting, cache, degradação controlada e isolamento de falhas
- 16.6 Estabelecer reference architectures, ADRs, guardrails técnicos e critérios de adoção para soluções corporativas de IA

**17. AI Ops, Evaluation & Security Básico + Intermediário + Avançado** *(próprio)*
- 17.1 Implementar observabilidade de IA com logs de prompts, respostas, traces, latência, custo, erros e feedback de usuários
- 17.2 Criar pipelines de avaliação com golden datasets, testes de regressão, métricas automáticas e revisão humana assistida
- 17.3 Avaliar qualidade de respostas com groundedness, relevância, completude, consistência, segurança e aderência ao formato
- 17.4 Automatizar quality gates para prompts, modelos, retrieval, agentes, ferramentas e releases de aplicações de IA
- 17.5 Aplicar segurança com validação de entrada, controle de saída, prompt injection defense, data leakage prevention e escopo de ferramentas
- 17.6 Monitorar produção com drift de comportamento, degradação de qualidade, abuso, custos, incidentes e resposta operacional

**18. Modelos & Inference Básico + Intermediário** *(referência → `ai-modelos-inference`, mesmo roadmap)*
- 18.1 Comparar modelos por janela de contexto, latência, custo, qualidade, multimodalidade e requisitos de implantação
- 18.2 Configurar parâmetros de inferência como temperature, top-p, max tokens, stop sequences e seed quando disponível
- 18.3 Implementar chamadas a APIs de modelos com autenticação, rate limits, retries, timeouts e tratamento de erros
- 18.4 Estruturar entradas e saídas com JSON schema, function calling, tool use e validação programática
- 18.5 Avaliar respostas de modelos com testes offline, golden datasets, métricas de qualidade e análise de falhas
- 18.6 Otimizar custo e desempenho com batching, caching, streaming, fallback de modelos e roteamento por tarefa

**19. Prompt Engineering & Interaction Básico + Intermediário** *(referência → `ai-prompt-engineering`, mesmo roadmap)*
- 19.1 Escrever prompts estruturados com objetivo, contexto, restrições, formato de saída e critérios de qualidade
- 19.2 Criar instruções reutilizáveis para tarefas de classificação, extração, sumarização, geração e transformação de texto
- 19.3 Aplicar few-shot prompting com exemplos positivos, negativos, contraexemplos e padrões de resposta esperados
- 19.4 Projetar fluxos conversacionais com memória de contexto, coleta incremental de informações e tratamento de ambiguidades
- 19.5 Implementar validação de saídas com rubricas, formatos estruturados, checagem de consistência e retry orientado
- 19.6 Reduzir alucinações com grounding, delimitação de fontes, perguntas de clarificação e verificação de evidências

**20. Memory & Retrieval RAG Básico + Intermediário** *(referência → `ai-memory-retrieval-rag`, mesmo roadmap)*
- 20.1 Implementar pipelines de ingestão para documentos com parsing, limpeza, chunking, metadados e versionamento
- 20.2 Gerar embeddings e indexar conteúdos em bancos vetoriais com filtros, namespaces e estratégias de atualização
- 20.3 Construir fluxos RAG com retrieval, reranking, contexto controlado, citações e composição de resposta
- 20.4 Avaliar qualidade de recuperação com precision, recall, relevância, cobertura, groundedness e análise de falhas
- 20.5 Otimizar chunk size, overlap, top-k, filtros, hybrid search e estratégias de ranking por domínio
- 20.6 Implementar memória conversacional com histórico resumido, contexto persistido, expiração e isolamento por usuário

**21. Agentic Systems Básico + Intermediário** *(referência → `ai-agentic-systems`, mesmo roadmap)*
- 21.1 Projetar agentes com objetivos, instruções, ferramentas disponíveis, limites de execução e critérios de parada
- 21.2 Implementar tool calling com schemas, validação de argumentos, tratamento de erros e retorno estruturado
- 21.3 Criar fluxos multi-step com planejamento, execução, observação, revisão e controle de estado
- 21.4 Integrar agentes com APIs, bancos de dados, sistemas internos, filas e mecanismos de busca
- 21.5 Aplicar guardrails para permissões, escopo de ferramentas, validação de ações e prevenção de loops
- 21.6 Avaliar agentes com cenários de teste, traces, taxa de sucesso, custo, latência e análise de falhas

**22. Desenvolvimento de Software Avançado** *(referência → `desenvolvimento-software-avancado`, Software Engineer)*
- 22.1 Arquitetura de código clean code aplicado
- 22.2 Design orientado a domínio DDD nível prático
- 22.3 Concorrência e paralelismo
- 22.4 Profiling e otimização de performance
- 22.5 Testes avançados mock e integração
- 22.6 Resiliência retry timeout fallback
- 22.7 Refatoração de sistemas legados
- 22.8 Code review técnico profundo
- 22.9 Abstrações complexas interfaces e contratos

**23. Design de Software Avançado** *(referência → `design-software-avancado`, Software Engineer)*
- 23.1 Arquitetura limpa Clean Architecture
- 23.2 Arquitetura hexagonal
- 23.3 Design orientado a domínio DDD tático
- 23.4 Boundary e context mapping
- 23.5 Evolução de design em sistemas complexos
- 23.6 Trade offs arquiteturais
- 23.7 Design para escala e manutenção

**24. Design de Soluções Básico** *(referência → `design-solucoes-basico`, Software Engineer)*
- 24.1 Diferença monolito vs microservices
- 24.2 Conceito de APIs
- 24.3 Integração entre sistemas
- 24.4 Noção de escalabilidade
- 24.5 Comunicação síncrona vs assíncrona

**25. Design de Soluções Intermediário** *(referência → `design-solucoes-intermediario`, Software Engineer)*
- 25.1 Event driven architecture
- 25.2 Mensageria queues brokers
- 25.3 Consistência eventual
- 25.4 Estratégias de cache
- 25.5 Load balancing
- 25.6 Failover básico
- 25.7 Design orientado a domínio macro

## STAFF — STAFF Escala Organizacional

_Herda todo o bloco Sênior (por herança; não repetido abaixo)._


**26. Padronização de AI** *(próprio)*
- 26.1 Definir reference architectures para LLM apps, RAG, agentes e pipelines de inferência
- 26.2 Criar templates reutilizáveis para serviços de IA com logging, tracing, testes e deploy padronizados
- 26.3 Estabelecer padrões de integração com modelos via APIs, SDKs, gateways e abstrações internas
- 26.4 Padronizar contratos de entrada e saída para prompts, tools, embeddings, retrievers e agentes
- 26.5 Definir critérios técnicos para seleção de modelos, provedores, embeddings e vector databases
- 26.6 Criar guidelines de prompt engineering para versionamento, avaliação, fallback e reutilização
- 26.7 Estabelecer padrões de observabilidade para latência, custo, qualidade, segurança e uso de tokens
- 26.8 Implementar bibliotecas internas para reutilização de componentes de AI engineering
- 26.9 Definir padrões de CI/CD para aplicações de IA com validação automática de prompts, datasets e modelos
- 26.10 Criar catálogo técnico de componentes aprovados para construção de soluções de IA

**27. Arquitetura organizacional** *(próprio)*
- 27.1 Desenhar uma AI platform corporativa com serviços compartilhados para times de produto e engenharia
- 27.2 Definir topologias de arquitetura para centralização, federação e self-service de capacidades de IA
- 27.3 Criar operating model técnico para AI Engineering, Machine Learning, Dados, Segurança e Produto
- 27.4 Estabelecer processos de arquitetura para revisão, aprovação e evolução de soluções de IA em escala
- 27.5 Definir padrões de integração entre AI platform, data platform, cloud platform e sistemas corporativos
- 27.6 Criar modelo de ownership para componentes de IA, produtos internos, APIs, agentes e pipelines
- 27.7 Estruturar golden paths para acelerar entrega de soluções de IA com segurança e consistência
- 27.8 Definir estratégia de interoperabilidade entre provedores de LLM, ferramentas internas e sistemas legados
- 27.9 Criar mapas de dependência técnica para reduzir acoplamento entre aplicações de IA e plataformas centrais
- 27.10 Estabelecer roadmap arquitetural para evolução de IA corporativa orientado a escalabilidade, custo e risco

**28. Governança e escala** *(próprio)*
- 28.1 Implementar AI governance com políticas técnicas para uso de modelos, dados, prompts e agentes
- 28.2 Definir processos de model risk management para avaliação, aprovação e monitoramento de soluções de IA
- 28.3 Criar pipelines de avaliação contínua com métricas de qualidade, segurança, factualidade e custo
- 28.4 Implementar guardrails para proteção contra prompt injection, vazamento de dados e respostas inseguras
- 28.5 Definir políticas de acesso, segregação e auditoria para dados sensíveis usados em aplicações de IA
- 28.6 Criar mecanismos de FinOps para controle de custo por produto, time, modelo, endpoint e workload
- 28.7 Implementar dashboards executivos e técnicos para adoção, performance, risco e ROI de soluções de IA
- 28.8 Definir processos de lifecycle management para prompts, modelos, datasets, embeddings e agentes
- 28.9 Criar frameworks de compliance para IA alinhados a privacidade, segurança, auditoria e rastreabilidade
- 28.10 Estruturar operação multi-time para suporte, incident response e melhoria contínua de plataformas de IA
