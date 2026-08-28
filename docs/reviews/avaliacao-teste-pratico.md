# Avaliação do teste prático

## Escopo

Esta avaliação confronta a implementação exclusivamente com os requisitos do arquivo **Teste Prático – Desenvolvedor(a) de Integrações e Coleta de Dados Web**.

Não foram considerados requisitos adicionais de produção que não estejam no enunciado.

## Execução realizada

A aplicação foi executada conforme as instruções do README, utilizando Docker:

```bash
docker compose build
docker compose run --rm app python -m src.main
docker compose run --rm app python -m pytest -v
docker compose up -d
```

Resultado da coleta real, em 28/08/2026:

| Métrica | Resultado |
|---|---:|
| Registros encontrados | 100 |
| Registros únicos no banco | 100 |
| Páginas tentadas | 11 |
| Páginas concluídas | 11 |
| Páginas com erro | 0 |
| Retries | 0 |
| Erros de parser | 0 |
| Registros normalizados | 100 |
| Registros persistidos | 100 |
| Erros de normalização | 0 |
| Erros de persistência | 0 |
| Duração | 26,62 segundos |

Também foi confirmada a consistência básica do banco:

- 100 registros totais;
- 100 `pncp_id` distintos;
- 100 títulos preenchidos;
- 100 URLs preenchidas.

A API foi iniciada sobre o banco coletado e respondeu:

```json
{"status":"ok","database_records":100}
```

A listagem `GET /procurements?limit=2` também retornou registros completos.

A suíte automatizada executada no container apresentou:

```text
21 passed, 1 warning in 0.69s
```

O warning é uma `StarletteDeprecationWarning` relacionado ao uso de `httpx` pelo `TestClient`; não causou falha nos testes.

## Confronto com os requisitos

| Requisito | Avaliação | Evidência |
|---|---|---|
| Fonte pública com múltiplos registros | Atende | PNCP documentado no README e acessado pelo crawler. |
| Crawler ou scraper | Atende | Playwright em `src/crawlers/pncp_catalog.py` e parser em `src/scrapers/pncp.py`. |
| Pelo menos 5 campos por registro | Atende | São coletados 9 campos principais: ID, título, modalidade, data, órgão, cidade, UF, objeto e URL. |
| Mínimo de 100 registros | Atende | Execução real obteve 100 registros únicos em 11 páginas. |
| Paginação e descoberta | Atende | O crawler percorre páginas numeradas até atingir o limite de registros ou páginas. |
| Controle de registros repetidos | Atende | Deduplicação por `href` e `pncp_id`, inclusive entre páginas. |
| Estruturação e normalização | Atende | Tratamento de espaços, datas, localização, URLs e campos obrigatórios. |
| Persistência | Atende | SQLite com tabela criada automaticamente e dados persistidos. |
| Idempotência | Atende | `pncp_id` é chave primária; registros iguais são identificados como duplicados. |
| Timeout, HTTP e indisponibilidade temporária | Atende | Retries para timeout, HTTP 429 e HTTP 5xx, com backoff exponencial. |
| Falha isolada por página ou registro | Atende | Falhas são registradas e o processamento continua. |
| Alteração inesperada da página | Atende parcialmente | Erros de parser são capturados, mas algumas alterações de rótulos podem resultar em campos nulos sem falha explícita. |
| Controle de requisições | Atende | Intervalo entre páginas, limite de páginas e retry controlado. |
| Logs de execução | Atende | Logs registram início, fim, páginas, registros, duplicados e erros. |
| Consulta dos dados | Atende | API com listagem, consulta por ID, filtros e Swagger. |
| Execução facilitada | Atende parcialmente | Docker funciona; a coleta e a API são executadas em comandos separados. |
| Testes automatizados | Atende | 21 testes passaram, cobrindo parser, normalização, persistência, deduplicação e API. |
| README completo | Atende | Documenta solução, fonte, arquitetura, dados, execução, testes, limitações e decisões. |

## Nota

**Nota final: 9,3/10**

### Justificativa

O candidato atendeu integralmente os requisitos funcionais principais e comprovou a execução real da coleta mínima de 100 registros. A aplicação também passou por uma suíte de 21 testes automatizados e teve a API validada com os dados efetivamente coletados.

Os descontos são pequenos e estão concentrados em dois pontos:

1. o crawler não possui testes automatizados específicos para retries, timeout, falhas HTTP e continuidade entre páginas;
2. o fluxo Docker não realiza a coleta automaticamente no `docker compose up`, exigindo um comando separado para o crawler.

Há ainda uma limitação menor na detecção de mudanças estruturais do PNCP: alguns campos ausentes podem ser persistidos como nulos sem que a execução seja classificada como falha.

## Feedback ao candidato

Você entregou uma solução consistente e bem organizada para o escopo do teste. A separação entre crawler, parser, normalização, persistência e API facilita a leitura e demonstra boa compreensão de um pipeline de integração.

Os pontos mais fortes foram:

- escolha justificada de uma fonte pública adequada;
- coleta real de 100 registros únicos;
- normalização explícita dos dados;
- deduplicação por identificador oficial;
- tratamento de falhas temporárias com retry e backoff;
- logs úteis para acompanhar a execução;
- API funcional para consulta dos dados;
- testes automatizados passando;
- README detalhado e suficiente para reproduzir o projeto.

Como próximos aprimoramentos, recomendo adicionar testes do crawler com mocks de timeout, HTTP 429, HTTP 5xx e falha de página, além de tornar mais explícita a detecção de mudança no layout do PNCP. Também seria interessante oferecer um comando único para executar a coleta e iniciar a API, caso o projeto evolua para um fluxo operacional contínuo.

No conjunto, a entrega demonstra bom domínio de coleta web, processamento de dados, persistência e disponibilização de informações por API.
