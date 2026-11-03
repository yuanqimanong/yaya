# Exemplos de estudo em português brasileiro

Todos os casos abaixo são fictícios e servem apenas para estudo. Na revisão, use somente as informações de cada exemplo.

## 1. Ajustar um texto de finanças

Entrada: A receita do trimestre foi de R$ 1,2 milhão, 8% acima do mesmo trimestre do ano anterior. A margem bruta passou de 20% para 23%. A empresa avalia que a demanda pode se recuperar, mas não divulgou dados de pedidos.

Aceitável: A receita do trimestre foi de R$ 1,2 milhão, alta de 8% em relação ao mesmo trimestre do ano anterior. A margem bruta subiu de 20% para 23%, avanço de 3 pontos percentuais. A empresa avalia que a demanda pode se recuperar, mas não divulgou dados de pedidos.

Inaceitável: Os pedidos dispararam e confirmaram a recuperação da demanda.

Motivo: o aumento de pedidos não aparece na entrada, e uma expectativa incerta virou fato.

Nota: este pacote cobre apenas o português brasileiro. Em um texto de Portugal, “ficheiro”, “ecrã” e “telemóvel” permanecem como estão; a revisão não os converte em “arquivo”, “tela” e “celular”.

## 2. Ajustar um comentário de código

Entrada:

```python
def should_retry(status):
    # verifica de forma inteligente se a chamada precisa ser repetida
    return status == 429
```

Apenas o comentário muda: `# Retorna True quando o status é 429.`

Inaceitável: `# Repete a chamada automaticamente até o servidor responder.`

Motivo: o código só compara um valor; não repete a chamada, não define espera nem limite de tentativas. A função e o código não mudam.

## 3. Enxugar um prompt

Entrada: Você é o maior especialista do mundo em resumos. Mostre todo o seu talento e, com base apenas em {{text}}, resuma em 3 pontos, com no máximo 50 palavras cada. Se o material não for suficiente, faça uma pergunta e espere a resposta.

Aceitável: Com base apenas em {{text}}, resuma em 3 pontos, com no máximo 50 palavras cada. Se o material não for suficiente, faça uma única pergunta e aguarde a resposta.

Inaceitável: Use todo o seu conhecimento para explicar {{text}} em detalhes.

Motivo: a versão inaceitável perde a exigência de usar apenas o texto fornecido, os 3 pontos, o limite de 50 palavras e a condição de esperar a resposta; além disso, troca o resumo por uma explicação genérica.

## 4. Transferir o estilo de uma amostra

Amostra: Primeiro, confira se funciona. Se funcionar, procure o ponto lento. Não afirme o que ainda não testou.

Traços transferíveis: frases curtas, ordem clara, verbos diretos e incerteza preservada.

Nova tarefa: criar um prompt para examinar um log.

Aceitável: Primeiro, procure erros em {{log}}. Depois, ordene os registros por ordem de ocorrência. Use apenas o que está no log. Se algo não puder ser determinado, diga isso.

Inaceitável: Já analisei milhares de servidores, então posso garantir que vou encontrar a causa.

Motivo: a versão inaceitável inventa experiência e promete um resultado; isso não é transferência de estilo.
