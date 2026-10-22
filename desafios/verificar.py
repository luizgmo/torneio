#!/usr/bin/env python3
"""Confere todas as rodadas geradas em desafios/.

Uso:
  python3 desafios/verificar.py

Verifica, para cada pasta rodada_*:
  - se o texto claro tem 200..250 letras a-z;
  - se as cifras e chaves respeitam a fase e o orcamento;
  - se o texto cifrado do arquivo corresponde ao texto claro + cifras + chaves;
  - se os hashes e os campos do metadata.json batem com os arquivos.

Nao depende do simples.py.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORCAMENTO = {1: 16, 2: 24, 3: 32, 4: 40}


def atbash(t: bytes) -> bytes:
    return bytes(219 - b if 97 <= b <= 122 else b for b in t)


def cesar(t: bytes, k: int) -> bytes:
    return bytes((b - 97 + k) % 26 + 97 if 97 <= b <= 122 else b for b in t)


def vigenere(t: bytes, chave: bytes) -> bytes:
    k = [b - 97 for b in chave]
    return bytes(
        (b - 97 + k[i % len(k)]) % 26 + 97 if 97 <= b <= 122 else b
        for i, b in enumerate(t)
    )


def xor(t: bytes, chave: bytes) -> bytes:
    return bytes(b ^ chave[i % len(chave)] for i, b in enumerate(t))


def aplicar(t: bytes, cifras: list[str], chaves: dict[str, str]) -> bytes:
    for nome in cifras:
        if nome == "atbash":
            t = atbash(t)
        elif nome == "cesar":
            t = cesar(t, int(chaves["cesar"]))
        elif nome == "vigenere":
            t = vigenere(t, chaves["vigenere"].encode("ascii"))
        elif nome == "xor":
            t = xor(t, bytes.fromhex(chaves["xor"]))
        else:
            raise ValueError(f"cifra desconhecida: {nome}")
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
            raise ValueError(f"cifra desconhecida: {nome}")
    return total


def sha256(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def ler_cifrado(caminho: Path) -> bytes:
    """Le o arquivo como o regulamento manda: UTF-8 inteiro, sem strip()."""
    return bytes(ord(c) for c in caminho.read_bytes().decode("utf-8"))


def verificar_rodada(pasta: Path) -> list[str]:
    erros: list[str] = []
    meta_caminho = pasta / "metadata.json"
    if not meta_caminho.exists():
        return [f"{pasta.name}: falta metadata.json"]

    meta = json.loads(meta_caminho.read_text(encoding="utf-8"))
    fase = int(meta["fase"])
    cifras = list(meta["cifras_ordem"])
    chaves = dict(meta["chaves"])

    claro_caminho = pasta / "texto_claro.txt"
    cifrado_caminho = pasta / "texto_cifrado.txt"
    if not claro_caminho.exists():
        return [f"{pasta.name}: falta texto_claro.txt"]
    if not cifrado_caminho.exists():
        return [f"{pasta.name}: falta texto_cifrado.txt"]

    claro = claro_caminho.read_bytes()
    cifrado = ler_cifrado(cifrado_caminho)

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
        erros.append("XOR nao e a ultima cifra")
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

    bits = custo(cifras, chaves)
    if bits > ORCAMENTO[fase] + 1e-9:
        erros.append(f"custo {bits:.1f} > orcamento {ORCAMENTO[fase]} bits")
    if abs(bits - float(meta.get("custo_bits", -1))) > 1e-9:
        erros.append("custo_bits do metadata.json nao confere")
    if len(claro) != int(meta.get("comprimento_texto_claro", -1)):
        erros.append("comprimento_texto_claro do metadata.json nao confere")
    if meta.get("texto_claro") != claro.decode("ascii"):
        erros.append("texto_claro do metadata.json nao confere")
    chave_simples = ",".join(chaves[n] for n in cifras)
    if meta.get("chaves_formato_simples_py") != chave_simples:
        erros.append("chaves_formato_simples_py do metadata.json nao confere")

    esperado = aplicar(claro, cifras, chaves)
    if esperado != cifrado:
        erros.append("texto cifrado nao corresponde ao claro + cifras + chaves")
        if len(esperado) != len(cifrado):
            erros.append(
                f"tamanho decifrado {len(cifrado)} != esperado {len(esperado)}"
            )

    if meta.get("sha256_texto_claro_ascii") != sha256(claro):
        erros.append("hash do texto claro nao bate com metadata.json")
    if meta.get("sha256_bytes_cifrados") != sha256(esperado):
        erros.append("hash dos bytes cifrados nao bate")
    if meta.get("sha256_arquivo_cifrado") != sha256(cifrado_caminho.read_bytes()):
        erros.append("hash do arquivo cifrado nao bate")

    hex_caminho = pasta / "texto_cifrado_hex.txt"
    if not hex_caminho.exists():
        erros.append("falta texto_cifrado_hex.txt")
    else:
        try:
            if bytes.fromhex(hex_caminho.read_text(encoding="ascii").strip()) != esperado:
                erros.append("texto_cifrado_hex.txt nao corresponde aos bytes cifrados")
        except ValueError:
            erros.append("texto_cifrado_hex.txt nao e hexadecimal valido")

    # Se o desafio termina em letras, o arquivo deve ser exatamente letras a-z.
    termina_em_xor = bool(meta.get("termina_em_xor", cifras[-1] == "xor"))
    if not termina_em_xor and any(not (97 <= b <= 122) for b in cifrado):
        erros.append("desafio sem XOR no fim deveria ter apenas letras a-z")
    if termina_em_xor != (cifras[-1] == "xor"):
        erros.append("termina_em_xor do metadata.json nao confere")

    legivel = pasta / "texto_claro_legivel.txt"
    if legivel.exists():
        t = unicodedata.normalize("NFKD", legivel.read_text(encoding="utf-8"))
        t = t.encode("ascii", "ignore").decode("ascii").lower()
        t = re.sub(r"[^a-z]", "", t).encode("ascii")
        if t != claro:
            erros.append("texto_claro_legivel.txt nao normaliza para o texto claro")

    return erros


def main() -> int:
    pastas = sorted(p for p in BASE.glob("rodada_*") if p.is_dir())
    if not pastas:
        print("Nenhuma pasta rodada_* encontrada.")
        return 1

    falhou = False
    for pasta in pastas:
        erros = verificar_rodada(pasta)
        meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
        if erros:
            falhou = True
            print(f"{pasta.name}: INVALIDO")
            for e in erros:
                print(f"  - {e}")
        else:
            print(
                f"{pasta.name}: VALIDO | {meta['comprimento_texto_claro']} letras | "
                f"{','.join(meta['cifras_ordem'])} | "
                f"{meta['custo_bits']:.1f}/{meta['orcamento_bits']} bits | "
                f"sha256={meta['sha256_arquivo_cifrado'][:12]}..."
            )
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
