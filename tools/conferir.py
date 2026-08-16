#!/usr/bin/env python3
"""
Confere os lançamentos contra a página de cada empreendimento no marcotulio.pro.

    python3 tools/conferir.py

A REGRA: a página do empreendimento manda. Quando ela e a tabela de um guia de
região discordam, vale a página — é ela que está sendo mantida. (Em 16/08/2026
o guia da zona norte dizia "a partir de R$ 252 mil" para o Matíz enquanto a
página dele dizia "a partir de R$ 235 mil". Um dos dois estava velho.)

O que o script faz: baixa o `link` de cada lançamento, lê o <title> e a
meta description — que é onde ele coloca o número atual — e compara com o
`preco` do card. Também mostra a data de atualização declarada na página,
para você ver de relance o que mexeu desde a última vez.

Saída: sai com código 1 se achou divergência, 0 se está tudo alinhado.

Não escreve nada. Depois de conferir, ajuste dados/lancamentos.json à mão e
rode `python3 tools/gerar.py`.
"""

import json
import os
import re
import html
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# "R$ 234.500" e "R$ 235 mil" no mesmo texto. O grupo de milhar precisa ser
# \.\d{3} e não [.\d]{3}, senão "234.500" é lido como 234.50 -> 23450.
RE_BRL = re.compile(r'R\$\s?(\d{1,3}(?:\.\d{3})*)(\s?mil)?', re.I)
RE_DATA = re.compile(r'(?:atualizado em|Atualização de)\s+([\d]{1,2} de \w+ de \d{4})', re.I)


def baixa(url, tentativas=3):
    """curl porque é ele que enxerga o proxy do ambiente."""
    for _ in range(tentativas):
        r = subprocess.run(['curl', '-sS', '--retry', '2', '--max-time', '30', url],
                           capture_output=True, text=True)
        if r.returncode == 0 and len(r.stdout) > 500:
            return r.stdout
    return ''


def precos(texto):
    """Todo valor em reais citado no texto, normalizado."""
    fora = []
    for m in RE_BRL.finditer(texto):
        n = int(m.group(1).replace('.', ''))
        if m.group(2):        # "R$ 235 mil"
            n *= 1000
        if n >= 50000:        # abaixo disso é entrada, sinal, saldo — não é o imóvel
            fora.append(n)
    return sorted(set(fora))


def brl(v):
    return 'R$ %s' % format(v, ',d').replace(',', '.') if v else '—'


def main():
    os.chdir(RAIZ)
    cards = json.load(open('dados/lancamentos.json', encoding='utf-8'))

    print('Conferindo %d lançamentos contra a página de cada empreendimento.\n' % len(cards))
    print('%-28s %-13s %-13s %-8s %s'
          % ('EMPREENDIMENTO', 'CARD', 'PÁGINA', 'ESTADO', 'PÁGINA ATUALIZADA EM'))
    print('-' * 92)

    divergem, mudos = [], []
    for c in cards:
        s = baixa(c['link'])
        if not s:
            mudos.append(c['titulo'])
            print('%-28s %-13s %-13s %-8s %s'
                  % (c['titulo'][:27], brl(c.get('preco')), '?', 'SEM RESPOSTA', ''))
            continue

        titulo = re.search(r'<title>(.*?)</title>', s, re.S)
        desc = re.search(r'name="description" content="(.*?)"', s)
        cabeca = html.unescape((titulo.group(1) if titulo else '') + ' ' +
                               (desc.group(1) if desc else ''))
        # a data pode estar no corpo, então procura na página inteira
        corpo = re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', s)))
        data = RE_DATA.search(corpo)

        na_pagina = precos(cabeca)
        meu = c.get('preco')
        menor = na_pagina[0] if na_pagina else None

        if meu and menor and meu != menor:
            estado, ruim = 'DIVERGE', True
        elif meu and not menor:
            estado, ruim = 'só o card', True
        elif menor and not meu:
            estado, ruim = 'só a página', True
        else:
            estado, ruim = 'ok', False
        if ruim:
            divergem.append((c['titulo'], meu, menor))

        print('%-28s %-13s %-13s %-8s %s'
              % (c['titulo'][:27], brl(meu), brl(menor), estado,
                 data.group(1) if data else ''))

    print()
    if mudos:
        print('Não responderam (tente de novo): %s' % ', '.join(mudos))
    if divergem:
        print('%d divergência(s). A página manda — ajuste dados/lancamentos.json:' % len(divergem))
        for t, meu, dele in divergem:
            print('   %-28s card %s  ->  página %s' % (t, brl(meu), brl(dele)))
        print('\nDepois: python3 tools/gerar.py')
        return 1
    print('Tudo alinhado com as páginas dos empreendimentos.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
