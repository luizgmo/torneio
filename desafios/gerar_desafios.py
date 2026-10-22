#!/usr/bin/env python3
"""Gera as quatro rodadas (fases 1 a 4) do torneio.

Cada rodada fica em uma pasta propria com:
  - texto_claro.txt          (exatamente 200..250 letras a-z)
  - texto_claro_legivel.txt  (com espacos e pontuacao, para conferencia)
  - texto_cifrado.txt        (no formato do regulamento)
  - chaves_e_cifras.txt      (gabarito: cifras, chaves e comandos)
  - entrega_professor.txt    (folha pronta para entregar ao professor)
  - metadata.json            (dados, custos e hashes)
  - README.md                (folha de controle; contem cifras/chaves)

A escolha de cada fase prioriza a dificuldade pratica dentro do orcamento:
  fase 1: Vigenere de 3 letras = 14,1 / 16 bits
  fase 2: Vigenere de 5 letras = 23,5 / 24 bits
  fase 3: Vigenere de 5 letras + XOR de 1 byte = 31,5 / 32 bits
  fase 4: Vigenere de 5 letras + XOR de 2 bytes = 39,5 / 40 bits

O XOR fica sempre por ultimo. Os textos usam muitas letras raras para
atrapalhar a analise de frequencia; por isso o ataque por frequencia do
simples.py nao devolve o texto correto para estes desafios.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORCAMENTO = {1: 16, 2: 24, 3: 32, 4: 40}

# Textos escritos com pontuacao apenas para leitura. O arquivo texto_claro.txt
# recebe somente as letras a-z, como exige o regulamento.
RODADAS = [
    {
        "fase": 1,
        "legivel": (
            "O zelador do zoologico achou um kiwi exotico na caixa de xadrez. "
            "Chamou o coordenador do show de jazz, que esperava no taxi. "
            "Juntos fizeram um waffle com yakisoba e um festival para a zebra. "
            "O publico aplaudiu, mas o vento fez um ziguezague e derrubou o cartaz."
        ),
        "cifras": ["vigenere"],
        "chaves": {"vigenere": "zxk"},
    },
    {
        "fase": 2,
        "legivel": (
            "O instrutor de windsurf e o mestre de karate organizaram um festival "
            "com boxe, judo, skate, rapel e yoga. O quiosque vendia waffle, "
            "yakisoba e ketchup, enquanto o xilofone e o saxofone animavam o "
            "publico. No fim, o kayak virou atracao e o zumbi ganhou um kiwi."
        ),
        "cifras": ["vigenere"],
        "chaves": {"vigenere": "qywxz"},
    },
    {
        "fase": 3,
        "legivel": (
            "Na aula de musica, o professor falou do jazz, do rock, do funk, do "
            "soul, do blues, do reggae e do k-pop. Depois mostrou o xilofone, o "
            "saxofone e o teclado, e explicou como o samba, o forro, o frevo, o "
            "maracatu e o xote animam o publico. No fim, a turma fez um show com "
            "banjo, ukulele e cavaquinho."
        ),
        "cifras": ["vigenere", "xor"],
        "chaves": {"vigenere": "kwyzx", "xor": "9b"},
    },
    {
        "fase": 4,
        "legivel": (
            "Em Quioto comprei um quimono e um xilofone, e em Xangai provei "
            "yakisoba com ketchup. Depois segui para Wellington, onde vi um show "
            "de jazz e um jogo de boxe, e para Zanzibar, onde aluguei um kayak e "
            "um windsurf. Voltei para Kansas com um kiwi e um whisky."
        ),
        "cifras": ["vigenere", "xor"],
        "chaves": {"vigenere": "zxkwy", "xor": "b3e7"},
    },
]


def normalizar(texto: str) -> bytes:
    """Remove acentos, pontuacao e espacos; deixa apenas a-z."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z]", "", texto).encode("ascii")


def atbash(t: bytes) -> bytes:
    return bytes(219 - b if 97 <= b <= 122 else b for b in t)


def cesar(t: bytes, k: int) -> bytes:
    return bytes((b - 97 + k) % 26 + 97 if 97 <= b <= 122 else b for b in t)


def vigenere(t: bytes, chave: bytes, decifrar: bool = False) -> bytes:
    k = [b - 97 for b in chave]
    sinal = -1 if decifrar else 1
    return bytes(
        (b - 97 + sinal * k[i % len(k)]) % 26 + 97 if 97 <= b <= 122 else b
        for i, b in enumerate(t)
    )


def xor(t: bytes, chave: bytes) -> bytes:
    return bytes(b ^ chave[i % len(chave)] for i, b in enumerate(t))


def aplicar(
    t: bytes, cifras: list[str], chaves: dict[str, str], decifrar: bool = False
) -> bytes:
    for nome in (cifras[::-1] if decifrar else cifras):
        if nome == "atbash":
            t = atbash(t)
        elif nome == "cesar":
            k = int(chaves["cesar"])
            t = cesar(t, -k if decifrar else k)
        elif nome == "vigenere":
            t = vigenere(t, chaves["vigenere"].encode("ascii"), decifrar)
        elif nome == "xor":
            t = xor(t, bytes.fromhex(chaves["xor"]))
        else:
            raise ValueError(f"cifra nao implementada: {nome}")
    return t


def custo(cifras: list[str], chaves: dict[str, str]) -> float:
    total = 0.0
    for nome in cifras:
        if nome == "atbash":
            continue
        if nome == "cesar":
            total += 4.7
        elif nome == "vigenere":
            total += 4.7 * len(chaves["vigenere"])
        elif nome == "xor":
            total += 8 * len(bytes.fromhex(chaves["xor"]))
        else:
            raise ValueError(f"cifra nao implementada: {nome}")
    return total


def sha256(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def chaves_para_simples(cifras: list[str], chaves: dict[str, str]) -> str:
    return ",".join(chaves[n] for n in cifras)


def validar_regras(
    fase: int, claro: bytes, cifras: list[str], chaves: dict[str, str]
) -> None:
    erros: list[str] = []
    if not 200 <= len(claro) <= 250:
        erros.append(f"texto claro com {len(claro)} letras (regra: 200..250)")
    if any(not (97 <= b <= 122) for b in claro):
        erros.append("texto claro tem caractere fora de a-z")
    if len(set(cifras)) != len(cifras):
        erros.append("cifras repetidas")
    if fase <= 2 and len(cifras) != 1:
        erros.append(f"fase {fase}: use exatamente 1 cifra")
    if fase >= 3 and not 1 <= len(cifras) <= 2:
        erros.append(f"fase {fase}: use 1 ou 2 cifras")
    if "xor" in cifras and cifras[-1] != "xor":
        erros.append("XOR tem que ser a ultima cifra")
    if "vigenere" in cifras:
        chave = chaves["vigenere"]
        if not chave.isalpha() or not chave.islower() or len(chave) > 8:
            erros.append("chave Vigenere deve ter so a-z, minuscula, ate 8 letras")
    if "cesar" in cifras:
        k = int(chaves["cesar"])
        if not 1 <= k <= 25:
            erros.append("chave Cesar deve ser 1..25")
    if "xor" in cifras:
        try:
            bytes.fromhex(chaves["xor"])
        except ValueError:
            erros.append("chave XOR nao e hexadecimal")
    if custo(cifras, chaves) > ORCAMENTO[fase] + 1e-9:
        erros.append(
            f"orcamento: {custo(cifras, chaves):.1f} > {ORCAMENTO[fase]} bits"
        )
    if erros:
        raise SystemExit("; ".join(erros))


def descrever_cifras(cifras: list[str], chaves: dict[str, str]) -> str:
    partes = []
    for nome in cifras:
        if nome == "atbash":
            partes.append("atbash(-)")
        elif nome == "vigenere":
            partes.append(f"vigenere({chaves['vigenere']})")
        elif nome == "xor":
            partes.append(f"xor({chaves['xor']})")
        elif nome == "cesar":
            partes.append(f"cesar({chaves['cesar']})")
    return " -> ".join(partes)


def escrever_rodada(indice: int, dados: dict) -> dict:
    fase = dados["fase"]
    cifras = dados["cifras"]
    chaves = dados["chaves"]
    claro = normalizar(dados["legivel"])
    validar_regras(fase, claro, cifras, chaves)

    cifrado = aplicar(claro, cifras, chaves)
    # Decifra para conferir o caminho de volta.
    assert aplicar(cifrado, cifras, chaves, decifrar=True) == claro, (
        "ida e volta nao conferem"
    )

    termina_em_xor = cifras[-1] == "xor"
    if termina_em_xor:
        dados_cifrados = "".join(chr(b) for b in cifrado).encode("utf-8")
        formato = (
            "UTF-8; cada caractere representa um byte 0..255 do resultado. "
            "Ler o arquivo inteiro como bytes, sem remover quebras de linha."
        )
        explicacao_formato = (
            "O desafio termina em XOR. Cada byte resultante (0 a 255) foi gravado "
            "como o caractere de mesmo codigo em UTF-8, exatamente como no arquivo "
            "de exemplo do professor. Por isso o arquivo tem bytes acima de 127 e "
            "**deve ser lido por inteiro, como bytes**. Nao use `readlines()`, "
            "`splitlines()` nem remova quebras de linha no meio."
        )
    else:
        if any(not (97 <= b <= 122) for b in cifrado):
            raise SystemExit("texto cifrado sem XOR deveria ter apenas letras a-z")
        dados_cifrados = cifrado
        formato = "Texto em letras minusculas de a-z, sem quebra de linha no final."
        explicacao_formato = (
            "O desafio termina em letras. O arquivo contem o texto cifrado em "
            "letras minusculas de `a-z`, sem quebra de linha no final."
        )

    pasta = BASE / f"rodada_{indice}"
    pasta.mkdir(parents=True, exist_ok=True)

    arquivo_claro = pasta / "texto_claro.txt"
    arquivo_legivel = pasta / "texto_claro_legivel.txt"
    arquivo_cifrado = pasta / "texto_cifrado.txt"
    arquivo_hex = pasta / "texto_cifrado_hex.txt"
    arquivo_gabarito = pasta / "chaves_e_cifras.txt"
    arquivo_entrega = pasta / "entrega_professor.txt"
    arquivo_meta = pasta / "metadata.json"
    arquivo_readme = pasta / "README.md"

    arquivo_claro.write_bytes(claro)
    arquivo_legivel.write_text(dados["legivel"].strip() + "\n", encoding="utf-8")
    arquivo_cifrado.write_bytes(dados_cifrados)
    arquivo_hex.write_text(
        " ".join(f"{b:02x}" for b in cifrado) + "\n", encoding="ascii"
    )

    chave_simples = chaves_para_simples(cifras, chaves)
    lista_cifras = ",".join(cifras)
    bits = custo(cifras, chaves)
    descricao = descrever_cifras(cifras, chaves)

    comando_decifrar = (
        f'python3 ../../simples.py decifrar texto_cifrado.txt '
        f'"{lista_cifras}" "{chave_simples}"'
        if len(cifras) > 1
        else f"python3 ../../simples.py decifrar texto_cifrado.txt "
        f"{lista_cifras} {chave_simples}"
    )
    comando_validar = (
        f'python3 ../../simples.py validar {fase} texto_claro.txt '
        f'texto_cifrado.txt "{lista_cifras}" "{chave_simples}"'
        if len(cifras) > 1
        else f"python3 ../../simples.py validar {fase} texto_claro.txt "
        f"texto_cifrado.txt {lista_cifras} {chave_simples}"
    )

    linhas_gabarito = [
        f"RODADA {indice} - FASE {fase}",
        "=" * (len(f"RODADA {indice} - FASE {fase}")),
        "",
        f"Cifras (ordem de aplicacao): {lista_cifras}",
        f"Cifras em detalhe: {descricao}",
        f"Chaves (ordem, formato do simples.py): {chave_simples}",
        "",
    ]
    if "vigenere" in cifras:
        linhas_gabarito.append(
            f"Vigenere: {chaves['vigenere']} ({len(chaves['vigenere'])} letras, "
            f"{4.7 * len(chaves['vigenere']):.1f} bits)"
        )
    if "atbash" in cifras:
        linhas_gabarito.append("Atbash: sem chave (custo 0 bit)")
    if "cesar" in cifras:
        linhas_gabarito.append(f"Cesar: {chaves['cesar']} (4,7 bits)")
    if "xor" in cifras:
        hexa = chaves["xor"]
        bytes_sep = " ".join(hexa[i : i + 2] for i in range(0, len(hexa), 2))
        linhas_gabarito.append(
            f"XOR: {bytes_sep} ({len(bytes.fromhex(hexa))} byte(s), "
            f"{8 * len(bytes.fromhex(hexa))} bits)"
        )
    linhas_gabarito += [
        "",
        f"Custo total: {bits:.1f} / {ORCAMENTO[fase]} bits",
        f"Comprimento do texto claro: {len(claro)} letras",
        "",
        "Comando para decifrar com o simples.py:",
        f"  {comando_decifrar}",
        "",
        "Comando para validar com o simples.py:",
        f"  {comando_validar}",
        "",
        "ATENCAO: este arquivo e o gabarito. Nao publique.",
    ]
    arquivo_gabarito.write_text("\n".join(linhas_gabarito) + "\n", encoding="utf-8")

    entrega = [
        f"ENTREGA AO PROFESSOR - RODADA {indice} / FASE {fase}",
        "=" * (len(f"ENTREGA AO PROFESSOR - RODADA {indice} / FASE {fase}")),
        "",
        f"Texto claro (somente a-z, {len(claro)} letras):",
        claro.decode("ascii"),
        "",
        f"Cifras na ordem de aplicacao: {lista_cifras}",
        f"Chaves na ordem: {chave_simples}",
        f"Custo: {bits:.1f} / {ORCAMENTO[fase]} bits",
        "",
        "Texto cifrado: anexo texto_cifrado.txt",
        f"Formato: {formato}",
        f"SHA-256 do arquivo texto_cifrado.txt: {sha256(dados_cifrados)}",
        "",
        "Declaracao: o texto cifrado foi gerado aplicando as cifras acima, na",
        "ordem indicada, ao texto claro acima, com as chaves acima.",
        "",
    ]
    arquivo_entrega.write_text("\n".join(entrega), encoding="utf-8")

    meta = {
        "rodada": indice,
        "fase": fase,
        "orcamento_bits": ORCAMENTO[fase],
        "custo_bits": round(bits, 1),
        "orcamento_usado_percent": round(100 * bits / ORCAMENTO[fase], 2),
        "cifras_ordem": cifras,
        "cifras_detalhe": descricao,
        "chaves": chaves,
        "chaves_formato_simples_py": chave_simples,
        "termina_em_xor": termina_em_xor,
        "texto_claro": claro.decode("ascii"),
        "texto_claro_legivel": dados["legivel"].strip(),
        "comprimento_texto_claro": len(claro),
        "texto_cifrado_arquivo": "texto_cifrado.txt",
        "texto_cifrado_hex_arquivo": "texto_cifrado_hex.txt",
        "texto_cifrado_bytes_utf8": len(dados_cifrados),
        "formato_texto_cifrado": formato,
        "sha256_texto_claro_ascii": sha256(claro),
        "sha256_bytes_cifrados": sha256(cifrado),
        "sha256_arquivo_cifrado": sha256(dados_cifrados),
    }
    arquivo_meta.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    readme = f"""# Rodada {indice} - Fase {fase}

> **USO INTERNO / GABARITO.** Este README contém as cifras e as chaves.
> Não publique. Os únicos arquivos públicos desta pasta são `texto_cifrado.txt`
> e `texto_cifrado_hex.txt`.

**Orcamento:** {ORCAMENTO[fase]} bits  
**Cifras (na ordem):** `{lista_cifras}`  
**Custo:** {bits:.1f} bits ({100 * bits / ORCAMENTO[fase]:.0f}% do orcamento)  
**Texto claro:** {len(claro)} letras (regra: 200 a 250, somente `a-z`)  
**Texto cifrado:** `texto_cifrado.txt`

## Formato do texto cifrado

{explicacao_formato}

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
{comando_validar}
```

Saida esperada: `VALIDO`.

## Como decifrar (gabarito)

```bash
{comando_decifrar}
```

O comando usa o `simples.py` que esta duas pastas acima. Se estiver em outro
lugar, ajuste o caminho.

> **Regra do torneio:** durante as rodadas nao e permitido usar ferramentas
> prontas nem assistentes de IA. Use estes arquivos para preparar e conferir o
> desafio; a ferramenta de cifrar/decifrar deve ser a do seu grupo.
"""
    arquivo_readme.write_text(readme, encoding="utf-8")

    return {
        "rodada": indice,
        "fase": fase,
        "pasta": pasta.name,
        "letras": len(claro),
        "cifras": lista_cifras,
        "custo": bits,
        "orcamento": ORCAMENTO[fase],
        "chave": chave_simples,
        "sha256_texto_claro": meta["sha256_texto_claro_ascii"],
        "sha256_arquivo_cifrado": meta["sha256_arquivo_cifrado"],
    }


def main() -> None:
    resumo = [escrever_rodada(i, dados) for i, dados in enumerate(RODADAS, 1)]
    print("Rodadas geradas:")
    for r in resumo:
        print(
            f"  {r['pasta']}: fase {r['fase']} | {r['letras']} letras | "
            f"{r['cifras']} | {r['custo']:.1f}/{r['orcamento']} bits"
        )
        print(f"    chave (gabarito): {r['chave']}")
        print(f"    sha256 claro:     {r['sha256_texto_claro']}")
        print(f"    sha256 cifrado:   {r['sha256_arquivo_cifrado']}")


if __name__ == "__main__":
    main()
