# Checklist Técnico de Adequação LGPD (Gestor Jurídico)

> Status atual: **parcial** (há controles de segurança, mas não conformidade completa).

## 1) Governança e Base Legal

- [ ] Definir e documentar base legal por operação de tratamento (cadastro, processos, agenda, contratos, procurações).
- [ ] Publicar Política de Privacidade e Termo de Tratamento de Dados.
- [ ] Definir Encarregado (DPO) e canal de atendimento ao titular.
- [ ] Elaborar RIPD (Relatório de Impacto à Proteção de Dados).

## 2) Direitos do Titular

- [ ] Implementar fluxo de **acesso** aos dados do titular.
- [ ] Implementar fluxo de **correção** de dados incorretos.
- [ ] Implementar fluxo de **anonimização/exclusão** quando aplicável.
- [ ] Implementar fluxo de **portabilidade** (exportação estruturada).
- [ ] Registrar prazo e evidência de atendimento das solicitações.

## 3) Segurança da Informação

- [x] Senhas com hash para usuários principais.
- [x] Migração automática de senha legada em texto para hash no login.
- [x] Remoção de credencial fixa hardcoded (`admin123`) do código.
- [x] Cookies de sessão com `HttpOnly` e `SameSite`.
- [x] `SESSION_COOKIE_SECURE` condicionado por ambiente.
- [ ] Forçar HTTPS em produção (app e proxy).
- [ ] Implementar proteção CSRF robusta em formulários e endpoints sensíveis.
- [ ] Implementar política de senha forte (tamanho, complexidade, rotação quando necessário).
- [ ] Implementar rate-limit e bloqueio progressivo para tentativas de login.
- [ ] Revisar upload de arquivos (MIME real, antivírus, limite por tipo, isolamento).
- [ ] Criptografar dados sensíveis em repouso quando necessário (campos críticos).

## 4) Minimização e Retenção

- [ ] Revisar campos coletados e remover dados desnecessários.
- [ ] Definir política de retenção por tipo de dado (clientes, processos, anexos).
- [ ] Automatizar descarte/anonimização ao fim do prazo legal/contratual.
- [ ] Separar dados de teste e produção (sem dados reais em homologação).

## 5) Auditoria e Rastreabilidade

- [ ] Registrar logs de acesso/alteração em dados pessoais (quem, quando, o quê).
- [ ] Garantir trilha de auditoria para operações críticas.
- [ ] Definir retenção de logs e proteção contra alteração indevida.

## 6) Terceiros e Operadores

- [ ] Formalizar contrato com operadores (ex.: hospedagem, e-mail, banco).
- [ ] Confirmar medidas de segurança dos fornecedores.
- [ ] Documentar transferência internacional de dados, quando existir.

## 7) Continuidade e Incidentes

- [ ] Criar plano de resposta a incidentes de privacidade.
- [ ] Definir procedimento de notificação à ANPD e titulares.
- [ ] Testar backup/restauração com periodicidade e evidências.

---

## Prioridade Recomendada (próximos passos)

1. **Crítico imediato:** CSRF, HTTPS obrigatório em produção, rate-limit de login.
2. **Curto prazo:** fluxos de direitos do titular e política de retenção.
3. **Médio prazo:** auditoria detalhada, RIPD, governança formal completa.

> Observação: este checklist é técnico-operacional e **não substitui** parecer jurídico especializado.
