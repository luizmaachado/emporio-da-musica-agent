# 02 — Informações da loja

Endereço, horário e dados da empresa vêm do manual de políticas (PDF). A cada mensagem, as três seções do manual mais próximas em significado são anexadas ao prompt (busca semântica com `bge-m3`), e o agente responde só com base nelas. O cliente não vê o manual, então o agente nunca cita seção.

```
Você: Qual o endereço da loja?

Assistente: O endereço da Empório da Música é:  
**Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, 79202-333**  

Precisa de ajuda com algo mais? 😊

[trace] 45.9s, 0 tool call(s)
[trace]   grounding: no ungrounded prices or names found
```

```
Você: vocês abrem no sábado?

Assistente: Sim, estamos abertos no sábado das 09h às 13h. O atendimento via WhatsApp segue o mesmo horário. 😊

[trace] 16.6s, 0 tool call(s)
[trace]   grounding: no ungrounded prices or names found
```

```
Você: qual o CNPJ de vocês?

Assistente: O CNPJ da Empório da Música é **12.345.678/0001-90**. Estamos há mais de 13 anos no mercado, no centro de Campo Grande. Precisa de ajuda com algo específico?

[trace] 36.1s, 0 tool call(s)
[trace]   grounding: no ungrounded prices or names found
```

## Observações
- São três conversas separadas; nenhuma chama tool, porque a resposta está no manual.
- Erro do modelo no último exemplo: o manual diz "mais de 15 anos" e a loja foi fundada em 2008, mas o agente escreveu "mais de 13 anos". O CNPJ está certo. A conferência de fundamentação só confere preços e nomes em negrito, então não pega esse tipo de erro (limitação documentada).
- O agente informa os dias e o horário de funcionamento, mas não diz se a loja está aberta neste momento: ele não tem relógio.
