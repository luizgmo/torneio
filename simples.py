#!/usr/bin/env python3
"""Uso:
  python3 simples.py cifrar 3 claro.txt desafio.txt "vigenere,xor" "arq,dd"
  python3 simples.py decifrar desafio.txt "vigenere,xor" "arq,dd" [saida.txt]
  python3 simples.py validar 3 claro.txt desafio.txt "vigenere,xor" "arq,dd"
  python3 simples.py atacar 3 desafio.txt

Chaves: atbash=-  cesar=3  vigenere=arq  xor=dd (hex)  xor2=2
"""

import heapq
import itertools
import math
import re
import sys
import unicodedata
from array import array
from pathlib import Path

ORCAMENTO = {1: 16, 2: 24, 3: 32, 4: 40}
BASE = Path(__file__).resolve().parent

# Peso de cada ordem do modelo de lingua. O 4-grama e o que mais separa
# portugues de "quase portugues" (texto que so acertou as frequencias).
PESOS = (0.05, 0.10, 0.25, 0.60)
# Pesos do modelo de diferencas entre letras vizinhas, usado só para
# comparar chaves XOR quando há muitas opções. Ele não muda com César.
PESOS_REL = (0.05, 0.25, 0.70)
ALFA = 0.1          # suavizacao dos n-gramas
PENAL_NOLETRA = -15.0

# Frequencias das letras em ingles (%), so para os exemplos do professor.
EN = [8.167, 1.492, 2.782, 4.253, 12.702, 2.228, 2.015, 6.094, 6.966,
      0.153, 0.772, 4.025, 2.406, 6.749, 7.507, 1.929, 0.095, 5.987,
      6.327, 9.056, 2.758, 0.978, 2.360, 0.150, 1.974, 0.074]
LOG_EN = [math.log(f / 100) for f in EN]


def letra(b):
    return 97 <= b <= 122


def aprender(caminho):
    """Aprende frequencias e n-gramas (1 a 4 letras) de um texto."""
    bruto = Path(caminho).read_bytes()
    texto = unicodedata.normalize("NFKD", bruto.decode("utf-8", "ignore"))
    texto = texto.encode("ascii", "ignore").lower()
    letras = re.sub(rb"[^a-z]", b"", texto)

    c1 = [0] * 26
    for b in letras:
        c1[b - 97] += 1
    total = sum(c1)

    # Contagens de 2, 3 e 4 letras, indexadas como numero na base 26.
    c2, c3, c4 = [0] * 676, [0] * 17576, [0] * 456976
    for i in range(len(letras) - 1):
        c2[(letras[i] - 97) * 26 + letras[i + 1] - 97] += 1
    for i in range(len(letras) - 2):
        k = ((letras[i] - 97) * 26 + letras[i + 1] - 97) * 26 + letras[i + 2] - 97
        c3[k] += 1
    for i in range(len(letras) - 3):
        k = (((letras[i] - 97) * 26 + letras[i + 1] - 97) * 26
             + letras[i + 2] - 97) * 26 + letras[i + 3] - 97
        c4[k] += 1

    # Diferencas entre letras vizinhas (modulo 26). Um César desloca o texto
    # inteiro, mas nao muda essas diferencas; uma chave XOR errada muda.
    r1, r2, r3 = [0] * 26, [0] * 676, [0] * 17576
    for i in range(len(letras) - 3):
        a = (letras[i + 1] - letras[i]) % 26
        b = (letras[i + 2] - letras[i + 1]) % 26
        c = (letras[i + 3] - letras[i + 2]) % 26
        r1[a] += 1
        r2[a * 26 + b] += 1
        r3[(a * 26 + b) * 26 + c] += 1

    # Frequencias em porcentagem (usadas pelo chi-quadrado).
    freq = [100 * (c + 0.5) / (total + 13) for c in c1]
    # Probabilidades do modelo de lingua.
    p1 = [(c + 0.5) / (total + 13) for c in c1]
    p2 = [(c2[i] + ALFA) / (c1[i // 26] + ALFA * 26) for i in range(676)]
    p3 = [(c3[i] + ALFA) / (c2[i // 26] + ALFA * 26) for i in range(17576)]
    p4 = [(c4[i] + ALFA) / (c3[i // 26] + ALFA * 26) for i in range(456976)]

    # Uma tabela unica com a nota de TODOS os 4-gramas possiveis (26^4).
    # Assim a nota de um texto e so uma consulta por letra, sem recalcular
    # probabilidades nem ramificar por n-grama visto/nao visto.
    tab4 = array("f", [0.0]) * 456976
    for i in range(456976):
        tab4[i] = math.log(
            PESOS[0] * p1[i % 26] + PESOS[1] * p2[i % 676]
            + PESOS[2] * p3[i % 17576] + PESOS[3] * p4[i]
        )

    # Modelo mais suave, usado para procurar chaves: 4-grama visto usa a
    # interpolacao completa; 4-grama novo recua para o trigrama final. Esse
    # relevo mais liso ajuda a busca a sair de minimos locais.
    tab3 = [0.0] * 17576
    for tri in range(17576):
        tab3[tri] = math.log(
            (PESOS[0] * p1[tri % 26] + PESOS[1] * p2[tri % 676]
             + PESOS[2] * p3[tri]) / sum(PESOS[:3])
        )
    tab4b = {}
    for i, c in enumerate(c4):
        if c:
            tab4b[i] = math.log(
                PESOS[0] * p1[i % 26] + PESOS[1] * p2[i % 676]
                + PESOS[2] * p3[i % 17576]
                + PESOS[3] * (c + ALFA) / (c3[i // 26] + ALFA * 26)
            )

    # Tabela do modelo de diferencas: probabilidade do proximo passo relativo.
    q1 = [(r1[i] + ALFA) / (sum(r1) + ALFA * 26) for i in range(26)]
    q2 = [(r2[i] + ALFA) / (r1[i // 26] + ALFA * 26) for i in range(676)]
    q3 = [(r3[i] + ALFA) / (r2[i // 26] + ALFA * 26) for i in range(17576)]
    tabd = array("f", [0.0]) * 17576
    for i in range(17576):
        tabd[i] = math.log(
            PESOS_REL[0] * q1[i % 26] + PESOS_REL[1] * q2[i % 676]
            + PESOS_REL[2] * q3[i]
        )

    return freq, p1, tab4, tab3, tab4b, tabd, q1


try:
    PT, P1, TAB4, TAB3, TAB4B, TABD, Q1 = aprender(BASE / "portugues.txt")
except FileNotFoundError:
    sys.exit("Falta o arquivo portugues.txt na mesma pasta do simples.py")

LOG_PT = [math.log(p) for p in P1]
LOG_D = [math.log(q) for q in Q1]


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
    """Nota de 4-gramas: quanto maior (menos negativa), mais parece português.

    Usa uma tabela com a probabilidade interpolada de todos os 26^4 4-gramas.
    Como a nota é a média por letra, textos de tamanhos diferentes ficam
    comparáveis, e bytes que não são letra são punidos com força.
    """
    t = t.rstrip(b"\r\n")
    if not t:
        return -1e9
    total = 0.0
    ctx = 0          # últimas 3 letras, em base 26
    seguidas = 0     # quantas letras seguidas existem antes da atual
    for b in t:
        if letra(b):
            b3 = b - 97
            idx = ctx * 26 + b3
            if seguidas >= 3:
                total += TAB4[idx]
            else:
                total += LOG_PT[b3]
            ctx = idx % 17576
            seguidas += 1
        else:
            total += PENAL_NOLETRA
            ctx = 0
            seguidas = 0
    return total / len(t)


def nota_busca(t):
    """Versão mais suave da nota, usada para procurar chaves.

    Recua para o trigrama final quando o 4-grama não aparece no texto de
    referência. O relevo fica menos acidentado, o que ajuda o refino a não
    parar num mínimo local.
    """
    t = t.rstrip(b"\r\n")
    if not t:
        return -1e9
    total = 0.0
    ctx = 0
    seguidas = 0
    for b in t:
        if letra(b):
            b3 = b - 97
            idx = ctx * 26 + b3
            if seguidas >= 3:
                v = TAB4B.get(idx)
                total += v if v is not None else TAB3[idx % 17576]
            else:
                total += LOG_PT[b3]
            ctx = idx % 17576
            seguidas += 1
        else:
            total += PENAL_NOLETRA
            ctx = 0
            seguidas = 0
    return total / len(t)


def nota_rel(t):
    """Nota invariante a César, pelas diferenças entre letras vizinhas.

    Usada só para ordenar chaves XOR quando há muitas opções: o texto antes
    do XOR pode estar deslocado por um César, e a nota normal puniria a chave
    certa. As diferenças não mudam com César, então a chave certa se destaca.
    """
    t = t.rstrip(b"\r\n")
    if not t:
        return -1e9
    total = 0.0
    ctx = 0          # últimas 2 diferenças, em base 26
    seguidas = 0     # quantas diferenças seguidas existem
    anterior = -1
    for b in t:
        if letra(b):
            if anterior >= 0:
                d = (b - anterior) % 26
                idx = ctx * 26 + d
                if seguidas >= 2:
                    total += TABD[idx]
                else:
                    total += LOG_D[d]
                ctx = idx % 676
                seguidas += 1
            anterior = b
        else:
            total += PENAL_NOLETRA
            ctx = 0
            seguidas = 0
            anterior = -1
    return total / len(t)


def nota_en(t):
    """Nota só com as frequências do inglês (para os exemplos do professor)."""
    t = t.rstrip(b"\r\n")
    if not t:
        return -1e9
    total = 0.0
    for b in t:
        total += LOG_EN[b - 97] if letra(b) else PENAL_NOLETRA
    return total / len(t)


def pontuar(t):
    """Aceita português ou inglês; escolhe a nota mais alta."""
    return max(nota(t), nota_en(t))


def chi(t):
    """Compara as letras de t com as frequências aprendidas do português."""
    cont = [0] * 26
    n = 0
    for b in t:
        if letra(b):
            cont[b - 97] += 1
            n += 1
    if not n:
        return 1e9
    total = 0.0
    for i in range(26):
        esperado = PT[i] * n / 100
        total += (cont[i] - esperado) ** 2 / esperado
    return total


def chi_en(t):
    """Chi-quadrado contra as frequências do inglês."""
    cont = [0] * 26
    n = 0
    for b in t:
        if letra(b):
            cont[b - 97] += 1
            n += 1
    if not n:
        return 1e9
    total = 0.0
    for i in range(26):
        esperado = EN[i] * n / 100
        total += (cont[i] - esperado) ** 2 / esperado
    return total


def ajuste(t):
    """Nota barata para escolher o byte de uma coluna do XOR.

    Usa só a distribuição das letras e pune fortemente bytes que não são letra.
    """
    cont = [0] * 26
    n = 0
    ruins = 0
    for b in t:
        if letra(b):
            cont[b - 97] += 1
            n += 1
        else:
            ruins += 1
    if not n:
        return -1e9
    total = 0.0
    for i in range(26):
        esperado = PT[i] * n / 100
        total += (cont[i] - esperado) ** 2 / esperado
    return -total - 50 * ruins


def chave_por_frequencia(t, m, funcao=chi):
    """Chave de Vigenère de tamanho m por análise de frequência por coluna."""
    return bytes(
        97 + min(range(26), key=lambda s: funcao(cesar(t[j::m], -s)))
        for j in range(m)
    )


def refinar_vigenere(t, chave):
    """Ajusta a chave coluna a coluna para maximizar a nota de 4-gramas.

    A análise de frequência acerta a chave na maioria dos casos, mas colunas
    curtas (chaves longas em textos de 200 letras) podem errar. Aqui cada
    posição da chave é testada de novo, agora olhando o texto inteiro.
    """
    chave = bytearray(chave)
    m = len(chave)
    n = len(t)
    p = bytearray(vigenere(t, bytes(chave), True))
    melhor = nota_busca(bytes(p))
    for _ in range(2):
        mudou = False
        for j in range(m):
            pos = range(j, n, m)
            atual = chave[j]
            for s in range(97, 123):
                for i in pos:
                    p[i] = (t[i] - s) % 26 + 97
                sc = nota_busca(bytes(p))
                if sc > melhor + 1e-12:
                    melhor = sc
                    atual = s
                    mudou = True
            chave[j] = atual
            for i in pos:
                p[i] = (t[i] - atual) % 26 + 97
        if not mudou:
            break
    return bytes(chave), melhor


def vigenere_candidatos(t, maxm, ingles=True):
    """Testa chaves de 1 até maxm letras, em português e (opcional) inglês."""
    out = []
    for m in range(1, maxm + 1):
        chave = chave_por_frequencia(t, m, chi)
        if m >= 2:
            # Chaves de 1 letra já são cobertas pelos 26 Césares; das demais
            # cuida o refino por 4-gramas.
            chave, _ = refinar_vigenere(t, chave)
        p = vigenere(t, chave, True)
        out.append((pontuar(p), p, chave))

        if ingles:
            ke = chave_por_frequencia(t, m, chi_en)
            pe = vigenere(t, ke, True)
            out.append((pontuar(pe), pe, ke))
    return out


def vigenere_reforcado(t, maxm, ingles=True):
    """Segunda tentativa para chaves difíceis, com outros pontos de partida.

    Textos com muitas letras raras deixam a análise de frequência por coluna
    ruidosa. Partir de 'a'*m, de 'z'*m e das frequências do inglês dá caminhos
    diferentes para o refino e costuma escapar do mínimo local.
    """
    out = []
    for m in range(2, maxm + 1):
        melhor = None
        for inicio in (chave_por_frequencia(t, m, chi),
                       chave_por_frequencia(t, m, chi_en),
                       b"a" * m, b"z" * m):
            chave, sc = refinar_vigenere(t, inicio)
            if melhor is None or sc > melhor[0]:
                melhor = (sc, chave)
        chave = melhor[1]
        p = vigenere(t, chave, True)
        out.append((pontuar(p), p, chave))

        if ingles:
            ke = chave_por_frequencia(t, m, chi_en)
            pe = vigenere(t, ke, True)
            out.append((pontuar(pe), pe, ke))
    return out


def atacar_sem_xor(t, maxv, reforcar=True):
    """Candidatos com Atbash, César e Vigenère (sem XOR)."""
    out = [(pontuar(atbash(t)), atbash(t), (("atbash", None),))]
    for s in range(1, 26):
        p = cesar(t, -s)
        out.append((pontuar(p), p, (("cesar", s),)))
    for sc, p, k in vigenere_candidatos(t, maxv):
        out.append((sc, p, (("vigenere", k),)))

    # Também testa Atbash junto com César/Vigenère.
    d = atbash(t)
    for s in range(1, 26):
        p = cesar(d, -s)
        out.append((pontuar(p), p, (("cesar", s), ("atbash", None))))
    for sc, p, k in vigenere_candidatos(d, maxv, ingles=False):
        out.append((sc, p, (("vigenere", k), ("atbash", None))))

    # Se nada acima ficou com cara de português, vale uma segunda passada de
    # Vigenère com mais pontos de partida. Só acontece nos casos difíceis.
    if reforcar and maxv >= 2 and max(nota(p) for _, p, _ in out) < -3.2:
        for sc, p, k in vigenere_reforcado(t, maxv):
            out.append((sc, p, (("vigenere", k),)))
        for sc, p, k in vigenere_reforcado(d, maxv, ingles=False):
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


def opcoes_xor(t, L):
    """Bytes de chave, por coluna, que fazem a coluna do XOR virar só letras."""
    n = len(t)
    opcoes = []
    for j in range(L):
        s = set(range(256))
        for i in range(j, n, L):
            s &= {t[i] ^ v for v in range(97, 123)}
        if not s:
            return None
        opcoes.append(sorted(s))
    return opcoes


def chave_xor_inicial(t, L):
    """Chave XOR por coluna usando a distribuição das letras (barato)."""
    opcoes = opcoes_xor(t, L)
    if not opcoes:
        opcoes = [list(range(256)) for _ in range(L)]
    return bytes(
        max(op, key=lambda k: ajuste(bytes(t[i] ^ k for i in range(j, len(t), L))))
        for j, op in enumerate(opcoes)
    )


def refinar_xor(t, chave):
    """Ajusta a chave XOR coluna a coluna pela nota do texto inteiro."""
    chave = bytearray(chave)
    L = len(chave)
    n = len(t)
    p = bytearray(xor(t, bytes(chave)))
    melhor = nota(bytes(p))
    opcoes = opcoes_xor(t, L)
    if not opcoes:
        opcoes = [[k] for k in chave]
    for _ in range(2):
        mudou = False
        for j in range(L):
            pos = range(j, n, L)
            atual = chave[j]
            for k in opcoes[j]:
                for i in pos:
                    p[i] = t[i] ^ k
                sc = nota(bytes(p))
                if sc > melhor + 1e-12:
                    melhor = sc
                    atual = k
                    mudou = True
            chave[j] = atual
            for i in pos:
                p[i] = t[i] ^ atual
        if not mudou:
            break
    return bytes(chave), melhor


def atacar(t, fase, top=3):
    """Tenta descobrir o texto claro e as chaves, sem conhecê-las."""
    orc = ORCAMENTO[fase]
    maxv = min(8, int(orc // 4.7))
    maxx = min(5, int(orc // 8))
    candidatos = atacar_sem_xor(t, maxv, reforcar=False)
    melhor_direto = max(max(nota_busca(p), nota_en(p))
                        for _, p, _ in candidatos)

    if fase == 1:
        for k in range(4):
            p = xor2(t, k)
            candidatos.append((pontuar(p), p, (("xor2", k),)))

    # XOR sozinho: uma chave por coluna + refino pela nota do texto.
    for L in range(1, maxx + 1):
        ch, _ = refinar_xor(t, chave_xor_inicial(t, L))
        p = xor(t, ch)
        candidatos.append((pontuar(p), p, (("xor", ch),)))

    # XOR por último, atrás de Atbash, César ou Vigenère.
    if fase >= 3:
        # Se o cifrado já é só letras e a busca sem XOR achou um texto ótimo,
        # não vale perder tempo testando um XOR que quase certamente não existe.
        tudo_letras = all(letra(b) for b in t.rstrip(b"\r\n"))
        if not (tudo_letras and melhor_direto >= -2.8):
            for L in range(1, maxx + 1):
                resto = orc - 8 * L
                if resto < 0:
                    continue
                mv = min(8, int(resto // 4.7))
                opcoes = opcoes_xor(t, L)
                if not opcoes:
                    continue
                # Colunas com muitas opções são quase sempre lixo; guarda as
                # melhores para o produto não explodir. A nota considera também
                # o Atbash, porque o texto antes do XOR pode estar invertido.
                opcoes = [
                    op if len(op) <= 6 else
                    sorted(op, reverse=True,
                           key=lambda k, j=j: max(
                               ajuste(bytes(t[i] ^ k for i in range(j, len(t), L))),
                               ajuste(atbash(bytes(t[i] ^ k
                                                  for i in range(j, len(t), L))))))
                    [:6]
                    for j, op in enumerate(opcoes)
                ]
                chaves = itertools.product(*opcoes)
                total = 1
                for op in opcoes:
                    total *= len(op)
                if total > 64:
                    # A nota pelas diferenças não se abala com César/Atbash,
                    # então não descarta a chave certa só porque o texto ainda
                    # está deslocado. Custa o mesmo que a nota normal.
                    def barato(ch):
                        v = xor(t, bytes(ch))
                        return max(nota_rel(v), nota_rel(atbash(v)))
                    chaves = heapq.nlargest(16, chaves, key=barato)
                vistos = set()
                for ch in chaves:
                    ch = bytes(ch)
                    v = xor(t, ch)
                    if v in vistos:
                        continue
                    vistos.add(v)
                    for sc, p, ps in atacar_sem_xor(v, mv, reforcar=total <= 2):
                        candidatos.append((sc, p, ps + (("xor", ch),)))

    # Último recurso: se nem o XOR nem a primeira passada de Vigenère acharam
    # nada parecido com português, tenta as chaves difíceis com mais partidas.
    if maxv >= 2 and max(nota(p) for _, p, _ in candidatos) < -3.2:
        for sc, p, k in vigenere_reforcado(t, maxv):
            candidatos.append((sc, p, (("vigenere", k),)))
        for sc, p, k in vigenere_reforcado(atbash(t), maxv, ingles=False):
            candidatos.append((sc, p, (("vigenere", k), ("atbash", None))))

    # Escolhe o idioma do texto uma vez para o conjunto todo. Se a melhor
    # leitura em inglês for claramente melhor que a melhor em português, usa
    # o inglês; senão, português. Assim uma leitura "quase inglês" não passa
    # na frente do texto verdadeiro só por acertar as frequências das letras.
    notas_pt = [nota(p) for _, p, _ in candidatos]
    notas_en = [nota_en(p) for _, p, _ in candidatos]
    notas = notas_en if max(notas_en) > max(notas_pt) + 0.20 else notas_pt
    candidatos = [(notas[i], p, ps)
                  for i, (_, p, ps) in enumerate(candidatos)]
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
