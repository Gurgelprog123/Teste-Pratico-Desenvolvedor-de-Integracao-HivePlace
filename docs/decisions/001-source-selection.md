# ADR 001 — Seleção da fonte de dados

## Status

Aceita.

## Contexto

O objetivo do projeto era escolher uma fonte pública adequada para uma aplicação de coleta de dados web, com possibilidade de:

- coletar pelo menos 100 registros;
- navegar por múltiplas páginas;
- extrair campos relevantes;
- normalizar e persistir os dados;
- implementar deduplicação e idempotência;
- tratar falhas de rede e mudanças de estrutura;
- respeitar limitações e bloqueios da fonte.

Durante a etapa inicial foram avaliadas diferentes fontes antes da definição da solução final.

---

## Fontes avaliadas

### Pichau

A Pichau foi considerada inicialmente como fonte para coleta de produtos.

Durante os testes, requisições HTTP convencionais retornaram bloqueios HTTP 403 e mecanismos de proteção contra automação.

Também foram realizados testes com Playwright utilizando uma configuração padrão de navegador, sem técnicas de evasão.

A fonte continuou apresentando bloqueios e páginas de proteção.

Como o projeto não deveria implementar mecanismos para contornar CAPTCHA, autenticação ou bloqueios deliberados, a Pichau foi descartada.

---

### Terabyte

A Terabyte também foi avaliada como possível fonte de dados de produtos.

Requisições HTTP convencionais retornaram HTTP 403.

Com Playwright foi possível acessar inicialmente a página e realizar testes de extração, inclusive em páginas de detalhe.

Entretanto, após a navegação por múltiplas páginas de produtos, a fonte passou a apresentar CAPTCHA e bloqueios.

A alternativa foi descartada porque continuar exigiria mecanismos de evasão ou contorno de proteção, o que não fazia parte do escopo do projeto.

---

### Portal Nacional de Contratações Públicas — PNCP

O PNCP foi escolhido como fonte final.

A página utilizada é o catálogo público de Editais e Avisos de Contratações:

```text
https://pncp.gov.br/app/editais