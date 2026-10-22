# Rodada 1 - Fase 1

> **USO INTERNO / GABARITO.** Este README contém as cifras e as chaves.
> Não publique. Os únicos arquivos públicos desta pasta são `texto_cifrado.txt`
> e `texto_cifrado_hex.txt`.

**Orcamento:** 16 bits  
**Cifras (na ordem):** `vigenere`  
**Custo:** 14.1 bits (88% do orcamento)  
**Texto claro:** 208 letras (regra: 200 a 250, somente `a-z`)  
**Texto cifrado:** `texto_cifrado.txt`

## Formato do texto cifrado

O desafio termina em letras. O arquivo contem o texto cifrado em letras minusculas de `a-z`, sem quebra de linha no final.

## Arquivos desta pasta

| Arquivo | Uso |
|---|---|
| `texto_cifrado.txt` | **Publico.** E o desafio que pode ser entregue aos outros grupos. |
| `texto_cifrado_hex.txt` | **Publico.** Os mesmos bytes do cifrado em hexadecimal, para conferencia. |
| `texto_claro.txt` | Gabarito: o texto claro exato, sem espacos nem pontuacao. Nao publicar antes da hora. |
| `texto_claro_legivel.txt` | Mesmo texto com espacos e pontuacao, so para conferir a leitura. |
| `entrega_professor.txt` | Folha pronta para entregar: texto claro, cifras, chaves, custo e hash. Nao publicar. |
| `chaves_e_cifras.txt` | Gabarito: cifras, chaves, custo e comandos. Nao publicar. |
| `metadata.json` | Dados completos, incluindo chaves e hashes. Nao publicar. |
| `README.md` | Esta folha de controle. Contem cifras/chaves. Nao publicar. |

## Como validar

Dentro desta pasta:

```bash
python3 ../../simples.py validar 1 texto_claro.txt texto_cifrado.txt vigenere zxk
```

Saida esperada: `VALIDO`.

## Como decifrar (gabarito)

```bash
python3 ../../simples.py decifrar texto_cifrado.txt vigenere zxk
```

O comando usa o `simples.py` que esta duas pastas acima. Se estiver em outro
lugar, ajuste o caminho.

> **Regra do torneio:** durante as rodadas nao e permitido usar ferramentas
> prontas nem assistentes de IA. Use estes arquivos para preparar e conferir o
> desafio; a ferramenta de cifrar/decifrar deve ser a do seu grupo.
