# Proposta de evolução: Browser Harness no crawler

## Objetivo

Este documento complementa a avaliação do teste prático com uma sugestão de evolução baseada no projeto [browser-use/browser-harness](https://github.com/browser-use/browser-harness).

A proposta não faz parte dos requisitos originais e não altera a nota de 9,3/10 atribuída à entrega. O objetivo é indicar como o candidato poderia ampliar a resiliência e a capacidade de manutenção do crawler aproveitando os conhecimentos demonstrados neste projeto.

## O que foi analisado

Na versão analisada, o Browser Harness:

- conecta um agente a um navegador por CDP;
- utiliza um daemon para manter a sessão do navegador;
- disponibiliza helpers reutilizáveis para navegação, inspeção, espera, JavaScript e screenshots;
- recomenda a árvore de acessibilidade para localizar elementos;
- permite criar helpers específicos de domínio em um workspace separado;
- possui diagnóstico de conexão e suporte a gravações opcionais.

Ele é apresentado como um harness de controle e exploração de navegador, não como uma biblioteca compatível diretamente com o objeto `Page` síncrono usado atualmente pelo Playwright.

## Leitura aplicada ao projeto atual

O crawler atual já possui uma boa propriedade para uma coleta reprodutível: o fluxo de produção é determinístico. Ele navega pelas páginas do PNCP, extrai os cards com seletores conhecidos e passa os dados para parser, normalizador e repository.

Por isso, a recomendação é **não substituir imediatamente o Playwright pelo Browser Harness**. Uma substituição direta introduziria:

- dependência de um daemon e de uma sessão CDP;
- uma camada adicional de instalação e operação;
- necessidade de adaptar o código que hoje recebe `playwright.sync_api.Page`;
- potencial comportamento não determinístico se um agente LLM decidir como localizar ou interpretar os cards;
- maior dificuldade para testar e reproduzir a coleta em CI.

## Evolução proposta

### 1. Criar um modo de exploração e diagnóstico

Adicionar um modo separado, executado sob demanda, para investigar alterações no PNCP usando Browser Harness.

Esse modo poderia:

1. conectar-se a um Chromium isolado por CDP;
2. abrir a página do catálogo;
3. aguardar a renderização;
4. inspecionar `page_info()`, árvore de acessibilidade e DOM;
5. localizar os elementos equivalentes aos cards de contratação;
6. capturar uma amostra de HTML, texto e screenshot;
7. gerar um relatório comparável com as fixtures atuais.

O resultado seria usado para atualizar o parser de forma consciente, sem colocar uma decisão de agente no caminho crítico de persistência.

### 2. Extrair um helper específico do PNCP

Criar um helper de domínio, por exemplo `pncp_catalog_helpers.py`, no workspace editável do harness, responsável por:

- localizar o catálogo;
- aguardar a lista de contratações;
- identificar a paginação;
- coletar os textos e links dos cards;
- retornar uma estrutura intermediária para inspeção.

Esse helper deveria ser pequeno, versionado separadamente do núcleo do harness e utilizado inicialmente para diagnóstico e geração de fixtures.

### 3. Manter o crawler determinístico como caminho principal

O `PncpCatalogCrawler` atual continuaria sendo o coletor padrão. O Browser Harness entraria como ferramenta de:

- descoberta inicial;
- investigação de layout;
- teste exploratório;
- geração de evidências visuais;
- recuperação operacional assistida, apenas quando autorizada.

Uma possível arquitetura futura seria:

```text
                 ┌──────────────────────────────┐
                 │ Browser Harness / CDP        │
                 │ exploração e diagnóstico     │
                 └──────────────┬───────────────┘
                                │ fixtures/relatório
                                ▼
PNCP ──► Playwright ──► parser determinístico ──► normalização ──► SQLite
```

### 4. Usar acessibilidade e estado da página como sinais de contrato

Em vez de depender somente de `a[href^="/editais/"]`, o modo exploratório poderia registrar sinais como:

- nome e papel dos elementos na árvore de acessibilidade;
- quantidade de cards encontrados;
- texto dos rótulos esperados;
- URL da página atual;
- presença de controle de paginação;
- amostra do DOM renderizado.

Esses sinais poderiam alimentar um teste de contrato que falha quando a página carrega, mas deixa de apresentar a estrutura esperada.

## Exemplo de desenho de integração futura

Uma implementação posterior poderia introduzir uma abstração de coleta:

```text
CatalogSource
├── PlaywrightPncpSource       # produção determinística
└── BrowserHarnessPncpProbe    # exploração/diagnóstico opcional
```

As duas implementações poderiam produzir o mesmo formato intermediário, por exemplo:

```text
RawProcurementCandidate {
    href,
    text,
    source_url,
    page_number,
    capture_metadata
}
```

O parser e o normalizador permaneceriam compartilhados. Assim, a adoção do harness ampliaria a capacidade de investigação sem duplicar as regras de negócio nem alterar a chave de deduplicação.

## Limites e cuidados

- O Browser Harness deve ser usado somente em páginas públicas e dentro das políticas do PNCP.
- A proposta não inclui CAPTCHA solving, stealth, proxies ou contorno de bloqueios.
- Gravações devem permanecer desabilitadas por padrão, pois screenshots e traces podem conter dados da página.
- Um agente LLM não deve decidir sozinho quais registros serão persistidos.
- O caminho de coleta deve continuar reproduzível sem uma sessão pessoal do Chrome.
- A adoção deve ser opcional para não tornar a API dependente do daemon CDP.
- A nova dependência só deveria ser adicionada depois de um spike validando instalação, licença, suporte no Docker e execução em CI.

## Critérios de aceitação sugeridos

Uma futura implementação poderia ser considerada pronta quando:

1. o crawler atual continuar funcionando sem Browser Harness;
2. o modo de diagnóstico conseguir abrir o catálogo em Chromium isolado;
3. o probe identificar a quantidade de cards e a paginação;
4. a saída do probe puder gerar ou atualizar uma fixture local;
5. houver teste comparando a fixture gerada com o parser existente;
6. uma alteração de layout produzir alerta explícito;
7. a coleta de 100 registros continuar passando sem depender de intervenção manual;
8. documentação explicar como executar o modo exploratório e como desligá-lo.

## Ganho esperado

Essa evolução traria ao projeto conhecimentos importantes do Browser Harness:

- inspeção por CDP;
- uso da acessibilidade como mecanismo de localização;
- helpers específicos de domínio;
- diagnóstico de sessões de navegador;
- evidências visuais e estruturais para manutenção do scraper;
- separação entre exploração assistida e execução determinística.

O ganho principal não seria simplesmente trocar uma biblioteca por outra. Seria transformar mudanças no layout do PNCP em um problema observável, com evidências e fixtures, reduzindo a chance de uma quebra silenciosa do parser.

## Feedback adicional ao candidato

O projeto já demonstra domínio suficiente de Playwright para cumprir o teste. Como próximo passo, recomendo estudar o Browser Harness como uma camada de engenharia de manutenção do crawler: use-o para explorar a interface, entender a árvore de acessibilidade, criar helpers específicos do PNCP e produzir evidências que ajudem a atualizar o parser.

A melhor evolução é preservar a simplicidade e a previsibilidade da coleta principal, incorporando o harness de forma incremental e opcional. Essa abordagem mostra maturidade ao reconhecer que uma ferramenta de exploração orientada por agente pode ser muito útil para descobrir mudanças, mas não precisa substituir um pipeline determinístico que já atende aos requisitos e foi validado com 100 registros.
