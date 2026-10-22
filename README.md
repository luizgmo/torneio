# Torneio de Criptografia — ferramenta simples

`simples.py` é um programa em Python, sem bibliotecas externas, que:

- cifra e decifra com **XOR, Atbash, César e Vigenère**;
- lê e grava o texto cifrado no formato do regulamento;
- confere o orçamento e as regras da fase;
- **ataca** um desafio, tentando descobrir o texto claro e as chaves.

## Requisito

Python 3.10 ou mais novo:

```bash
python3 --version
```

## Como rodar

Abra o terminal na pasta do projeto:

```bash
cd ~/Área\ de\ Trabalho/cript
python3 simples.py
```

Sem argumentos, ele mostra o resumo dos comandos.

## Decifrar

Quando você já sabe a cifra e a chave:

```bash
python3 simples.py decifrar ARQUIVO CIFRAS CHAVES
```

Exemplos com os arquivos do professor:

```bash
python3 simples.py decifrar caesar_criptografado.txt cesar 3
python3 simples.py decifrar atbash_criptografado.txt atbash -
python3 simples.py decifrar crypt_vigenere.txt vigenere arq
python3 simples.py decifrar xor_criptografado.txt xor dd
```

Para gravar o resultado:

```bash
python3 simples.py decifrar xor_criptografado.txt xor dd resultado.txt
```

## Cifrar

```bash
python3 simples.py cifrar FASE CLARO SAIDA CIFRAS CHAVES
```

Exemplo:

```bash
python3 simples.py cifrar 1 data.txt meu_desafio.txt cesar 3
```

Com duas cifras (XOR sempre por último):

```bash
python3 simples.py cifrar 3 meu_texto.txt desafio.txt "vigenere,xor" "arq,dd"
```

## Validar

```bash
python3 simples.py validar 3 meu_texto.txt desafio.txt "vigenere,xor" "arq,dd"
```

Saída: `VALIDO` ou a lista de problemas.

## Atacar

```bash
python3 simples.py atacar FASE ARQUIVO [QUANTIDADE]
```

Exemplos:

```bash
python3 simples.py atacar 1 caesar_criptografado.txt
python3 simples.py atacar 1 xor_criptografado.txt
python3 simples.py atacar 4 desafio.txt 5
```

Para testar um desafio em português, use o `exemplo.txt`:

```bash
python3 simples.py cifrar 4 exemplo.txt desafio.txt "vigenere,xor" "arq,0a1b"
python3 simples.py atacar 4 desafio.txt
```

Saída esperada:

```text
#1 nota -2.16 | 30.1 bits | vigenere(arq) -> xor(0a1b)
hojeacordeicedoefuicaminharnoparque...
```

Ele mostra os candidatos ordenados por nota, com as cifras e chaves encontradas:

```text
#1 nota -3.35 | 4.7 bits | cesar(3)
thequickbrownfoxjumpsoverthelazydog...
```

O ataque funciona para:

- uma cifra (Atbash, César, Vigenère, XOR e XOR de 2 bits);
- duas cifras nas fases 3 e 4, incluindo XOR por último.

Ele aprende um modelo de língua de 4-gramas a partir do arquivo
`portugues.txt` e usa a restrição de que o texto claro tem só letras `a-z`.
Para achar Vigenère e XOR, testa as chaves coluna a coluna, refina as melhores
e só então compara os candidatos pelo modelo completo. Não é força bruta cega:
os casos comuns rodam em menos de um segundo e as combinações mais difíceis
das fases 3 e 4 ficam em poucos segundos.

Os exemplos `atbash_criptografado.txt`, `caesar_criptografado.txt`,
`crypt_vigenere.txt` e `xor_criptografado.txt` do professor estão em inglês.
Além do modelo de português, o ataque tem um modelo simples de frequências do
inglês e escolhe sozinho a leitura que parece melhor, então também acerta
esses quatro arquivos:

```bash
python3 simples.py atacar 1 crypt_vigenere.txt
#1 ... | vigenere(arq)
```

Um texto de referência maior ajuda até certo ponto: os 4-gramas já ficam
estáveis com algumas dezenas de milhares de letras. O `portugues.txt` atual
tem cerca de 57 KB, o que é suficiente. Para o torneio, o importante é o texto
de referência ser em português; misturar inglês com português pode piorar os
resultados.

## Testar o ataque

```bash
python3 testar_ataque.py
```

A bateria testa todas as cifras e combinações válidas das fases 1 a 4, chaves
XOR com bytes baixos ou zero, as rodadas atuais em `desafios/` e os exemplos do
professor. Leva de 1 a 2 minutos; o argumento opcional muda quantos textos são
usados por combinação:

```bash
python3 testar_ataque.py 1   # mais rápido
python3 testar_ataque.py 5   # mais completo
```

## Chaves

| Cifra | Exemplo | Observação |
|---|---|---|
| `atbash` | `-` | não tem chave |
| `cesar` ou `caesar` | `3` | 1 a 25 |
| `vigenere` | `arq` | até 8 letras |
| `xor` | `dd` | hexadecimal |
| `xor2` | `2` | só fase 1 |

Use aspas quando houver vírgula: `"vigenere,xor"` e `"arq,dd"`.

## Fases

| Fase | Orçamento | Cifras por desafio |
|---|---|---|
| 1 | 16 bits | 1 |
| 2 | 24 bits | 1 |
| 3 | 32 bits | 1 ou 2 |
| 4 | 40 bits | 1 ou 2 |

## Arquivos de exemplo

- `data.txt` — texto claro de exemplo (em inglês).
- `exemplo.txt` — texto claro de exemplo em português, com 230 letras.
- `portugues.txt` — texto em português usado para o ataque aprender os
  4-gramas e as diferenças entre letras. Tem cerca de 57 KB: o
  regulamento mais um trecho de *Dom Casmurro* (Machado de Assis, domínio
  público). Pode ser trocado por outro texto em português, sem acentos ou com
  acentos (o programa remove os acentos).
- `atbash_criptografado.txt`, `caesar_criptografado.txt`,
  `crypt_vigenere.txt`, `xor_criptografado.txt` — desafios de exemplo.
- `testar_ataque.py` — bateria que confere o ataque em todas as combinações.
- `keys` — chaves dos exemplos.
- `Torneio de Criptografia Regulamento.pdf` — regulamento.

## Aviso

O regulamento exige que cada grupo desenvolva a própria ferramenta e proíbe
usar ferramentas prontas ou assistentes de IA durante o torneio. Use este
programa para estudar e testar; confirme com o professor o que é permitido.
