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
python3 simples.py atacar 1 crypt_vigenere.txt
python3 simples.py atacar 4 desafio.txt 5
```

Ele mostra os candidatos ordenados por nota, com as cifras e chaves encontradas:

```text
#1 nota -3.04 | 4.70 bits | cesar(3)
thequickbrownfoxjumpsoverthelazydog...
```

O ataque funciona para:

- uma cifra (Atbash, César, Vigenère, XOR e XOR de 2 bits);
- duas cifras nas fases 3 e 4, incluindo XOR por último.

Ele usa frequência de letras, pedaços comuns de palavras e a restrição de que o
texto claro tem só letras `a-z`. Não é força bruta cega, então roda em menos de
alguns segundos.

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

- `data.txt` — texto claro de exemplo.
- `atbash_criptografado.txt`, `caesar_criptografado.txt`,
  `crypt_vigenere.txt`, `xor_criptografado.txt` — desafios de exemplo.
- `keys` — chaves dos exemplos.
- `Torneio de Criptografia Regulamento.pdf` — regulamento.

## Aviso

O regulamento exige que cada grupo desenvolva a própria ferramenta e proíbe
usar ferramentas prontas ou assistentes de IA durante o torneio. Use este
programa para estudar e testar; confirme com o professor o que é permitido.
