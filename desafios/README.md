# Desafios do torneio — 4 rodadas (fases 1 a 4)

Esta pasta contém uma rodada completa para cada fase do torneio. Cada
`rodada_N/` é autossuficiente: tem o texto claro, a versão legível, as cifras, as
chaves, os comandos, o texto cifrado, os hashes e um README.

## Resumo

| Pasta | Fase | Orçamento | Cifras (ordem) | Custo | Chave (gabarito) | Letras | Cifrado |
|---|---:|---:|---|---:|---|---:|---|
| `rodada_1/` | 1 | 16 bits | `vigenere` | 14,1 bits | `zxk` | 208 | letras |
| `rodada_2/` | 2 | 24 bits | `vigenere` | 23,5 bits | `qywxz` | 205 | letras |
| `rodada_3/` | 3 | 32 bits | `vigenere,xor` | 31,5 bits | `kwyzx,9b` | 221 | bytes |
| `rodada_4/` | 4 | 40 bits | `vigenere,xor` | 39,5 bits | `zxkwy,b3e7` | 200 | bytes |

> **Gabarito.** As chaves acima e todos os outros arquivos de cada pasta
> (`texto_claro.txt`, `texto_claro_legivel.txt`, `chaves_e_cifras.txt`,
> `entrega_professor.txt`, `metadata.json`, `README.md`) são para uso interno.
> Publique apenas o texto cifrado (`texto_cifrado.txt` e, se quiser,
> `texto_cifrado_hex.txt`) durante a rodada. Entregue ao professor o texto claro,
> as cifras, as chaves e o texto cifrado, como manda o regulamento.

## Por que estas escolhas são difíceis

### O detalhe que muita gente esquece: XOR puro vaza a chave

O texto claro só tem letras `a-z` (códigos 97 a 122), todos com o bit mais
significativo igual a 0. Ao aplicar XOR com um byte de chave, **todos os bytes
daquela coluna herdam o bit mais significativo da chave**. Ou seja, o texto
cifrado revela de graça 1 bit de cada byte da chave XOR. Pior: como o texto claro
só pode ter letras, a condição "o resultado tem que cair em `a-z`" muitas vezes
determina o byte da chave de forma única, sem nem precisar de análise de
frequência. Por isso um XOR de 2, 3 ou 5 bytes é bem mais fraco do que o número
de bits sugere.

O Vigenère não tem esse vazamento: o texto cifrado é letra, a chave é um
deslocamento, e o fato de o resultado ser letra não entrega a chave. O ataque
real é de frequência, e é aí que o texto escolhido ajuda.

| Fase | Escolha atual | Bits efetivos* | Alternativa de orçamento máximo | Bits efetivos* |
|---|---|---:|---|---:|
| 1 | Vigenère de 3 letras | 14,1 | XOR de 2 bytes | 14,0 |
| 2 | Vigenère de 5 letras | 23,5 | XOR de 3 bytes | 21,0 |
| 3 | Vigenère 5 + XOR 1 byte | 30,5 | Atbash + XOR 4 bytes | 28,0 |
| 4 | Vigenère 5 + XOR 2 bytes | 37,5 | Atbash + XOR 5 bytes | 35,0 |

\* Estimativa conservadora: o Vigenère mantém os 4,7 bits por letra; o XOR perde
1 bit por byte por causa do vazamento do bit mais significativo. O Atbash custa
0. Na prática, o XOR pode ser ainda mais fraco por causa da restrição "o texto
claro só tem letras".

### As quatro escolhas

- **Fase 1:** Vigenère de 3 letras (`zxk`), custo **14,1 / 16 bits**. É a maior
  chave de Vigenère que cabe em 16 bits. Um XOR de 2 bytes gastaria 16 bits, mas
  seria mais fácil de quebrar pelo motivo acima.
- **Fase 2:** Vigenère de 5 letras (`qywxz`), custo **23,5 / 24 bits**. É a maior
  chave de Vigenère que cabe em 24 bits, e usa quase todo o orçamento.
- **Fase 3:** Vigenère de 5 letras + XOR de 1 byte (`kwyzx` e `9b`), custo
  **31,5 / 32 bits**. Duas camadas, com o XOR por último, como exige a regra.
- **Fase 4:** Vigenère de 5 letras + XOR de 2 bytes (`zxkwy` e `b3e7`), custo
  **39,5 / 40 bits**. Duas camadas, XOR por último, quase 100% do orçamento.

O regulamento impõe um **teto** de bits, não a obrigação de gastar todos. "Bits
que não forem usados se perdem" significa que não dá para guardar para a fase
seguinte; não significa que gastar mais bits sempre deixa o desafio mais difícil.
Aqui a prioridade foi a dificuldade prática.

### Os textos

- Têm entre **200 e 221 letras**, perto do mínimo permitido (200). A rodada 4,
  que tem a camada XOR mais longa, usa exatamente 200 letras: menos texto,
  menos amostras por coluna para a análise de frequência.
- Usam **muitas letras raras** (`k`, `w`, `y`, `x`, `z`, `j`), o que achata a
  distribuição das letras em relação ao português comum. Isso atrapalha
  justamente o ataque de frequência.
- Continuam em português, com frases que fazem sentido, sem acentos, sem espaços,
  sem números e sem pontuação dentro do arquivo `texto_claro.txt`.
- Cada rodada tem um tema diferente, para que o texto claro de uma fase não
  ajude a adivinhar o da seguinte.

### Teste com o ataque do `simples.py`

Rodando `python3 simples.py atacar FASE texto_cifrado.txt 3` nas quatro pastas,
o ataque **não devolve o texto claro correto nem a chave correta** entre os três
primeiros candidatos. Na verdade, a heurística de frequência por coluna escolhe
o deslocamento errado, então a chave correta nem entra na lista de candidatos.
Ele até encontra candidatos que "parecem português" pela contagem de letras, mas
erra a chave. Isso não prova que os desafios são impossíveis: uma ferramenta
melhor ou mais tempo pode resolvê-los. Mas é um bom sinal de que eles são bem
mais difíceis do que os desafios de exemplo do professor.

> **Se você quiser a versão 100% do orçamento declarado**, ela é possível:
> XOR de 2 bytes (fase 1), XOR de 3 bytes (fase 2), Atbash + XOR de 4 bytes
> (fase 3) e Atbash + XOR de 5 bytes (fase 4). Essas versões usam 16/24/32/40
> bits, mas o ataque do `simples.py` as resolve rapidamente. As versões atuais
> trocam alguns décimos ou poucos bits por uma dificuldade prática bem maior.

## O que tem em cada pasta

| Arquivo | Conteúdo |
|---|---|
| `texto_cifrado.txt` | O desafio em si. Pode ser publicado. |
| `texto_cifrado_hex.txt` | Os mesmos bytes do cifrado em hexadecimal, para conferência. Também pode ser publicado. |
| `texto_claro.txt` | Texto claro exato: só letras `a-z`, sem espaços nem quebra de linha. |
| `texto_claro_legivel.txt` | O mesmo texto com espaços e pontuação, para conferência. |
| `entrega_professor.txt` | Folha pronta para entregar: texto claro, cifras, chaves, custo e hash. |
| `chaves_e_cifras.txt` | Cifras na ordem, chaves em hexadecimal/letras, custo e comandos. |
| `metadata.json` | Fase, orçamento, custo, chaves, comprimentos e hashes SHA-256. |
| `README.md` | Folha de controle da rodada. Contém cifras/chaves; não publicar. |

## Formato do texto cifrado

- **Fases 1 e 2:** o desafio termina em Vigenère. O arquivo contém o texto
  cifrado em letras minúsculas de `a-z`, sem quebra de linha no final.
- **Fases 3 e 4:** o desafio termina em XOR. Cada byte resultante (0 a 255) foi
  gravado como o caractere de mesmo código em UTF-8, exatamente como no arquivo
  de exemplo do professor. Por isso o arquivo tem bytes acima de 127 e **deve
  ser lido por inteiro, como bytes**. Não use `readlines()`, `splitlines()` nem
  remova quebras de linha no meio.

## Conferir tudo

Na raiz do projeto:

```bash
python3 desafios/verificar.py
```

Saída esperada:

```text
rodada_1: VALIDO | 208 letras | vigenere | 14.1/16 bits | sha256=...
rodada_2: VALIDO | 205 letras | vigenere | 23.5/24 bits | sha256=...
rodada_3: VALIDO | 221 letras | vigenere,xor | 31.5/32 bits | sha256=...
rodada_4: VALIDO | 200 letras | vigenere,xor | 39.5/40 bits | sha256=...
```

Também dá para conferir com o `simples.py` do professor. Exemplos:

```bash
cd desafios/rodada_1
python3 ../../simples.py validar 1 texto_claro.txt texto_cifrado.txt vigenere zxk

cd ../rodada_3
python3 ../../simples.py validar 3 texto_claro.txt texto_cifrado.txt "vigenere,xor" "kwyzx,9b"
```

Para decifrar e ver o texto claro:

```bash
cd desafios/rodada_4
python3 ../../simples.py decifrar texto_cifrado.txt "vigenere,xor" "zxkwy,b3e7"
```

## Regerar ou criar mais rodadas

O script `gerar_desafios.py` recria as quatro pastas e sobrescreve os arquivos:

```bash
python3 desafios/gerar_desafios.py
```

Para criar uma rodada extra, copie a pasta da fase desejada e troque o texto e
as chaves **mantendo o custo dentro do orçamento**. Nas fases 1 e 2 use uma cifra
só; nas fases 3 e 4 use até duas, com o XOR sempre por último. O texto claro
precisa ter entre 200 e 250 letras `a-z`, em português.

> **Aviso do regulamento:** durante o torneio não é permitido usar ferramentas
> prontas, sites, bibliotecas que já implementem as cifras/ataques, nem
> assistentes de IA. Estes arquivos servem para preparar e conferir os desafios;
> a ferramenta usada nos ataques deve ser a desenvolvida pelo grupo.
