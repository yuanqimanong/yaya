# Ejemplos de aprendizaje en español

Todos los casos son material didáctico ficticio. Para reescribir, usa solo la información que aparece en cada ejemplo.

## 1. Ajustar un texto financiero

Entrada: Los ingresos del trimestre fueron de 1,2 millones de euros, un 8 % más que en el mismo periodo del año anterior. El margen bruto pasó del 20 % al 23 %. La empresa cree que la demanda podría recuperarse, pero no ha facilitado datos de pedidos.

Revisión aceptable: Los ingresos del trimestre fueron de 1,2 millones de euros, un 8 % más que en el mismo periodo del año anterior. El margen bruto pasó del 20 % al 23 %, es decir, 3 puntos porcentuales. La empresa cree que la demanda podría recuperarse, pero no ha facilitado datos de pedidos.

Revisión inaceptable: Los pedidos se dispararon y confirman una recuperación sólida de la demanda.

Motivo: la entrada no menciona ningún aumento de pedidos. La revisión inaceptable inventa ese dato y convierte una previsión incierta en un hecho.

Nota regional: se conservan la coma decimal, el espacio antes del signo de porcentaje y el léxico del original, en este caso propios de España. Si el texto llegara de México con 1.2 millones y 8%, se mantendrían ese punto decimal y esa ausencia de espacio. Tampoco se sustituye el vocabulario local (por ejemplo, «computadora» por «ordenador») ni las formas de trato.

## 2. Ajustar un comentario de código

Entrada:

```python
def should_retry(status):
    # Aquí se comprueba de forma inteligente si hace falta reintentar
    return status == 429
```

Solo el comentario: `# Indica si conviene reintentar: True cuando el estado es 429.`

Inaceptable: `# Reintenta automáticamente hasta que el servidor responda bien.`

Motivo: la función solo compara un valor y devuelve un booleano; no reintenta, no espera y no fija un número de intentos. El código y el nombre de la función no se tocan.

## 3. Reducir una instrucción sin perder condiciones

Entrada: Eres un redactor experto de nivel mundial. Aprovecha al máximo tu capacidad y resume {{text}} en 3 puntos, con un máximo de 50 palabras por punto. Usa únicamente la información del texto. Si el material no alcanza, haz una sola pregunta y espera la respuesta antes de continuar.

Aceptable: Resume {{text}} en 3 puntos de 50 palabras como máximo cada uno. Usa solo la información del texto. Si el material no alcanza, haz una sola pregunta y espera la respuesta antes de resumir.

Inaceptable: Resume el texto con tus conocimientos y añade contexto útil.

Motivo: la versión inaceptable pierde la variable, el límite de la fuente, el número de puntos, la extensión y la condición de preguntar y esperar.

## 4. Trasladar el estilo de una muestra

Muestra: Antes de publicar, revisa la cifra. Si no cuadra, busca el origen. Lo que no puedas comprobar, déjalo fuera.

Rasgos transferibles: frases cortas, orden explícito, verbos directos y una duda que no se disimula.

Nuevo encargo: crear una instrucción para revisar un registro con {{log}}.

Aceptable: Primero, busca los errores en {{log}}. Luego, ordénalos por aparición. Usa solo lo que diga el registro. Lo que no pueda confirmarse, señálalo.

Inaceptable: He revisado miles de servidores y puedo identificar la causa de cualquier fallo.

Motivo: la versión inaceptable inventa experiencia y capacidad; no traslada el estilo, sino una identidad falsa.
