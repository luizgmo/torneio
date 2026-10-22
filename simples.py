#!/usr/bin/env python3
"""Uso:
  python3 simples.py cifrar 3 claro.txt desafio.txt "vigenere,xor" "arq,dd"
  python3 simples.py decifrar desafio.txt "vigenere,xor" "arq,dd" [saida.txt]
  python3 simples.py validar 3 claro.txt desafio.txt "vigenere,xor" "arq,dd"
  python3 simples.py atacar 3 desafio.txt

Chaves: atbash=-  cesar=3  vigenere=arq  xor=dd (hex)  xor2=2
"""

import itertools
import math
import sys
from pathlib import Path

ORCAMENTO = {1: 16, 2: 24, 3: 32, 4: 40}

# Frequências das letras (%), em português e inglês.
PT = (14.63, 1.04, 3.88, 4.99, 12.57, 1.02, 1.30, 1.28, 6.18, 0.40, 0.02,
      2.78, 4.74, 5.05, 10.73, 2.52, 1.20, 6.53, 7.81, 4.34, 4.63, 1.67,
      0.01, 0.21, 0.01, 0.47)
EN = (8.17, 1.49, 2.78, 4.25, 12.70, 2.23, 2.02, 6.09, 6.97, 0.15, 0.77,
      4.03, 2.41, 6.75, 7.51, 1.93, 0.10, 5.99, 6.33, 9.06, 2.76, 0.98,
      2.36, 0.15, 1.97, 0.07)
LOG_PT = [math.log(f / 100) for f in PT]
LOG_EN = [math.log(f / 100) for f in EN]

# Pedaços comuns de palavras, para diferenciar texto de verdade de lixo.
DOIS = set(b"de os as ar er ra es do da co ca po qu ue en te re se al nt st ta "
           b"to ad or ma me mo na no pr tr ir ou em am om um th he in an on at "
           b"nd ti of ed is it ng ha le ve ri ro ic ne ea ce li ch be si ur el "
           b"la ns di fo pe ec ct us ac il ly un".split())
TRES = set(b"que ent ara com est ado par men con nte ida dos das res sta cao oes "
           b"ica ico ura pro pre tra tri mos ram ssa sso ade the and ing her tha "
           b"int ere tio ter ers ati hat ate all ver his ont ion".split())


def letra(b):
    return 97 <= b <= 122


def atbash(t):
    return bytes(219 - b if letra(b) else b for b in t)


def cesar(t, k):
    return bytes((b - 97 + k) % 26 + 97 if letra(b) else b for b in t)


def vigenere(t, chave, decifrar=False):
    k = [b - 97 for b in chave]
    sinal = -1 if decifrar else 1
    return bytes((b - 97 + sinal * k[i % len(k)]) % 26 + 97 if letra(b) else b
                 for i, b in enumerate(t))


def xor(t, chave):
    return bytes(b ^ chave[i % len(chave)] for i, b in enumerate(t))


def xor2(t, k):
    return bytes((b & 252) | ((b & 3) ^ k) for b in t)


def aplicar(t, passos, decifrar=False):
    for nome, chave in (passos[::-1] if decifrar else passos):
        if nome == "atbash":
            t = atbash(t)
        elif nome == "cesar":
            t = cesar(t, -chave if decifrar else chave)
        elif nome == "vigenere":
            t = vigenere(t, chave, decifrar)
        elif nome == "xor":
            t = xor(t, chave)
        elif nome == "xor2":
            t = xor2(t, chave)
    return t


def custo(passos):
    total = 0
    for nome, chave in passos:
        if nome == "atbash":
            pass
        elif nome == "cesar":
            total += 4.7
        elif nome == "vigenere":
            total += 4.7 * len(chave)
        elif nome == "xor":
            total += 8 * len(chave)
        elif nome == "xor2":
            total += 2
    return total


def regras(passos, fase):
    nomes = [n for n, _ in passos]
    erros = []
    if len(set(nomes)) != len(nomes):
        erros.append("cifras repetidas")
    if fase <= 2 and len(passos) != 1:
        erros.append(f"fase {fase}: use 1 cifra")
    if fase >= 3 and not 1 <= len(passos) <= 2:
        erros.append(f"fase {fase}: use 1 ou 2 cifras")
    if "xor" in nomes and nomes[-1] != "xor":
        erros.append("XOR tem que ser a ultima cifra")
    if "xor2" in nomes and (fase != 1 or len(passos) != 1):
        erros.append("xor2 so vale sozinho na fase 1")
    if custo(passos) > ORCAMENTO[fase] + 1e-9:
        erros.append(f"orcamento: {custo(passos):.1f} > {ORCAMENTO[fase]} bits")
    return erros


def ler_claro(p):
    return Path(p).read_bytes().strip()


def ler_cifrado(p):
    s = Path(p).read_bytes().decode("utf-8")
    if s.endswith("\n"):
        s = s[:-1]
    return bytes(ord(c) for c in s)


def gravar(p, t, cifrado):
    if cifrado:
        Path(p).write_bytes("".join(chr(b) for b in t).encode("utf-8"))
    else:
        Path(p).write_bytes(t)


def chave(nome, s):
    if nome == "atbash":
        return None
    if nome in ("cesar", "caesar"):
        return int(s)
    if nome == "vigenere":
        return s.lower().encode()
    if nome == "xor":
        return bytes.fromhex(s)
    if nome == "xor2":
        return int(s)


def passos(cifras, chaves):
    nomes = ["cesar" if n.strip() == "caesar" else n.strip()
             for n in cifras.split(",")]
    return [(n, chave(n, k.strip()))
            for n, k in zip(nomes, chaves.split(","))]


def nota(t):
    """Dá uma nota para o texto: quanto maior, mais parece português/inglês."""
    t = t.rstrip(b"\r\n")
    if not t:
        return -1e9
    n = len(t)
    sp = se = 0.0
    ruins = 0
    for b in t:
        if letra(b):
            sp += LOG_PT[b - 97]
            se += LOG_EN[b - 97]
        else:
            ruins += 1
    bonus = sum(0.06 for i in range(n - 1) if t[i:i + 2] in DOIS)
    bonus += sum(0.12 for i in range(n - 2) if t[i:i + 3] in TRES)
    return max(sp, se) / n - 2 * ruins + bonus / n


def vigenere_candidatos(t, maxm):
    """Testa chaves de 1 até maxm letras.

    Para cada tamanho, escolhe em cada coluna o deslocamento que deixa
    aquela coluna com cara de português. É a análise de frequência clássica.
    """
    out = []
    for m in range(1, maxm + 1):
        chave = bytes(
            97 + max(range(26), key=lambda s: nota(cesar(t[j::m], -s)))
            for j in range(m)
        )
        p = vigenere(t, chave, True)
        out.append((nota(p), p, chave))
    return out


def atacar_sem_xor(t, maxv):
    """Candidatos com Atbash, César e Vigenère (sem XOR)."""
    out = [(nota(atbash(t)), atbash(t), (("atbash", None),))]
    for s in range(1, 26):
        p = cesar(t, -s)
        out.append((nota(p), p, (("cesar", s),)))
    for sc, p, k in vigenere_candidatos(t, maxv):
        out.append((sc, p, (("vigenere", k),)))

    # Também testa Atbash junto com César/Vigenère.
    d = atbash(t)
    for s in range(1, 26):
        p = cesar(d, -s)
        out.append((nota(p), p, (("cesar", s), ("atbash", None))))
    for sc, p, k in vigenere_candidatos(d, maxv):
        out.append((sc, p, (("vigenere", k), ("atbash", None))))
    return out


def descrever(passos):
    partes = []
    for nome, chave in passos:
        if nome == "atbash":
            partes.append("atbash")
        elif nome == "vigenere":
            partes.append("vigenere(" + chave.decode() + ")")
        elif nome == "xor":
            partes.append("xor(" + chave.hex() + ")")
        elif nome == "xor2":
            partes.append("xor2(" + str(chave) + ")")
        else:
            partes.append("cesar(" + str(chave) + ")")
    return " -> ".join(partes)


def atacar(t, fase, top=3):
    """Tenta descobrir o texto claro e as chaves, sem conhecê-las."""
    orc = ORCAMENTO[fase]
    maxv = min(8, int(orc // 4.7))
    maxx = min(5, int(orc // 8))
    candidatos = atacar_sem_xor(t, maxv)

    if fase == 1:
        for k in range(4):
            p = xor2(t, k)
            candidatos.append((nota(p), p, (("xor2", k),)))

    for L in range(1, maxx + 1):
        ch = bytes(max(range(256), key=lambda k: nota(bytes(b ^ k for b in t[j::L])))
                   for j in range(L))
        p = xor(t, ch)
        candidatos.append((nota(p), p, (("xor", ch),)))

    if fase >= 3:
        for L in range(1, maxx + 1):
            resto = orc - 8 * L
            if resto < 0:
                continue
            mv = min(8, int(resto // 4.7))
            opcoes = []
            for j in range(L):
                s = set(range(256))
                for i in range(j, len(t), L):
                    s &= {t[i] ^ v for v in range(97, 123)}
                if not s:
                    break
                opcoes.append(sorted(s))
            else:
                for ch in itertools.product(*opcoes):
                    ch = bytes(ch)
                    v = xor(t, ch)
                    if any(not letra(b) for b in v.rstrip(b"\r\n")):
                        continue
                    for sc, p, ps in atacar_sem_xor(v, mv):
                        candidatos.append((sc, p, ps + (("xor", ch),)))

    candidatos.sort(reverse=True, key=lambda x: x[0])
    vistos = set()
    saida = []
    for sc, p, ps in candidatos:
        if p in vistos or regras(ps, fase):
            continue
        vistos.add(p)
        saida.append((sc, p, ps))
        if len(saida) >= top:
            break
    return saida


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return

    if a[0] == "cifrar":
        fase, entrada, saida, cifras, chaves = a[1:6]
        ps = passos(cifras, chaves)
        t = ler_claro(entrada)
        erros = regras(ps, int(fase))
        if not 200 <= len(t) <= 250:
            erros.append(f"texto com {len(t)} caracteres (regra: 200..250)")
        if any(not letra(b) for b in t):
            erros.append("texto claro deve ter so letras a-z")
        if erros:
            print("Aviso:", *erros, sep="\n  ")
        gravar(saida, aplicar(t, ps), True)
        print(f"ok: {saida} | {custo(ps):.1f}/{ORCAMENTO[int(fase)]} bits")

    elif a[0] == "decifrar":
        entrada, cifras, chaves = a[1:4]
        ps = passos(cifras, chaves)
        t = aplicar(ler_cifrado(entrada), ps, True)
        if len(a) > 4:
            gravar(a[4], t, False)
        else:
            print(t.decode("latin-1"))

    elif a[0] == "validar":
        fase, claro, cifrado, cifras, chaves = a[1:6]
        ps = passos(cifras, chaves)
        t = ler_claro(claro)
        erros = regras(ps, int(fase))
        if not 200 <= len(t) <= 250:
            erros.append("texto claro fora de 200..250")
        if aplicar(t, ps) != ler_cifrado(cifrado):
            erros.append("cifrado nao corresponde ao claro + chaves")
        print("VALIDO" if not erros else "INVALIDO: " + "; ".join(erros))

    elif a[0] == "atacar":
        fase = int(a[1])
        top = int(a[3]) if len(a) > 3 else 3
        resultados = atacar(ler_cifrado(a[2]), fase, top)
        if not resultados:
            print("Nada encontrado.")
        for i, (sc, p, ps) in enumerate(resultados, 1):
            print(f"\n#{i} nota {sc:.2f} | {custo(ps):.1f} bits | "
                  + descrever(ps))
            print(p.decode("latin-1"))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
