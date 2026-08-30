#!/usr/bin/env python3
"""
Gera o site a partir de uma fonte única de dados.

    python3 tools/gerar.py

Entradas   dados/imoveis.json      imóveis de captação própria
           dados/lancamentos.json  lançamentos de construtora
           dados/faq.json          perguntas e respostas
           dados/torrano.json      exclusivos da Torrano (link para o site deles)

Saídas     index.html              cards e schema.org escritos DENTRO do HTML
           imovel/<slug>/          uma página por imóvel
           sitemap.xml             todas as URLs do site

--------------------------------------------------------------------------------
POR QUE ISTO EXISTE

Antes, os imóveis só existiam dentro de um array JavaScript e os cards eram
criados no navegador. Quem lê a página sem executar JS — e é assim que a maior
parte do rastreamento acontece — via literalmente "Nenhum imóvel publicado
ainda". Medido em 16/08/2026, na página no ar: 163 KB de HTML e 11.237
caracteres de texto indexável, nenhum deles com o nome de um imóvel.

O Search Console do mesmo período conta a história inteira: 19 impressões,
0 cliques, uma única página indexada e uma única consulta, o próprio nome dele.
Site de uma página só = uma chance de ranquear.

Este script conserta as duas pontas:
  1. escreve os cards como HTML de verdade, que o rastreador lê sem JS;
  2. dá a cada imóvel uma URL própria, com title, descrição e schema seus.

O JavaScript da página continua existindo para busca, filtro e galeria — ele
passa a ENRIQUECER um HTML que já está pronto, em vez de criá-lo do zero.

--------------------------------------------------------------------------------
COMO O SCRIPT ESCREVE NO index.html

Só entre marcadores. Tudo que estiver fora deles nunca é tocado:

    <!-- @gerado:nome -->   ...conteúdo gerado...   <!-- @/gerado -->
    /* @gerado:nome */      ...conteúdo gerado...   /* @/gerado */

Se um marcador sumir, o script para e avisa em vez de adivinhar onde escrever.
"""

import datetime
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://imoveis.marcotulio.pro'
ZAP = '5534996778075'
# lastmod do sitemap. Chumbar a data faz o sitemap envelhecer sozinho e
# mentir para o buscador na próxima publicação. DATA=2026-01-31 no ambiente
# força um valor, para reproduzir uma geração antiga.
HOJE = os.environ.get('DATA') or datetime.date.today().isoformat()

# As quatro regiões, na ordem em que aparecem na página. O guia de cada uma
# mora no marcotulio.pro — aqui a gente lista e manda para lá, em vez de
# repetir o texto (conteúdo repetido concorre com a própria página dele).
REGIOES = [
    {
        'id': 'oeste', 'nome': 'Zona Oeste',
        'resumo': 'Onde estão os preços mais baixos da cidade e o maior volume de lançamento.',
        'guia': 'https://marcotulio.pro/blog/apartamentos-zona-oeste-uberlandia',
        'bairros': [
            'Chácaras Tubalina e Quartel', 'Tubalina', 'Jardim Holanda', 'Mansour',
            'Luizote de Freitas', 'Loteamento Residencial Pequis', 'Planalto',
            'Jardim Patrícia', 'Jardim Patricia', 'Fruta do Conde', 'Jardim Canaã',
            'Monte Hebron',
            'Jardim das Palmeiras', 'Jardim América', 'Jardim Ipanema', 'Guarani',
            'Dona Zulmira', 'Taiaman', 'Morada do Sol', 'City Uberlândia',
            'Copacabana', 'Jaraguá', 'Pampulha',
        ],
    },
    {
        'id': 'sul', 'nome': 'Zona Sul',
        'resumo': 'A região mais desejada da cidade, agora ligada pelo Anel Viário Sul.',
        'guia': 'https://marcotulio.pro/blog/apartamentos-zona-sul-uberlandia',
        'bairros': [
            'Gávea', 'Gávea Sul', 'Jardim Karaíba', 'Morada da Colina', 'Cidade Jardim',
            'São Jorge', 'Shopping Park', 'Jardim Sul', 'Jardim Inconfidência',
            'Jardim Inconfidencia', 'Jardim Botânico', 'Nova Uberlândia', 'Morada Nova',
            'Laranjeiras', 'Portal do Vale', 'Vida Nova', 'Jardim Europa', 'Jardim Veneza',
            'Cond. Paradiso Ecológico', 'Morada dos Pássaros', 'Bosque dos Buritis', 'Gsp',
            'EcoPark', 'Eco Park', 'Jardim Espanha', 'Parque Una',
        ],
    },
    {
        'id': 'leste', 'nome': 'Zona Leste',
        'resumo': 'Morumbi, Novo Mundo e Granja Marileusa — o maior número de lançamentos mapeados.',
        'guia': 'https://marcotulio.pro/blog/apartamentos-zona-leste-uberlandia',
        'bairros': [
            'Morumbi', 'Novo Mundo', 'Granja Marileusa', 'Tibery', 'Alvorada',
            'Grand Ville', 'Santa Mônica', 'Segismundo Pereira', 'Custódio Pereira',
            'Aclimação', 'Umuarama', 'Alto Umuarama', 'Quinta Alto Umuarama',
            'Integração', 'Joana D’Arc', 'Dom Almir', 'Prosperidade', 'São Gabriel',
        ],
    },
    {
        'id': 'norte', 'nome': 'Zona Norte',
        'resumo': 'A região com menos lançamento da cidade — e metragem maior pelo mesmo dinheiro.',
        'guia': 'https://marcotulio.pro/blog/apartamentos-zona-norte-uberlandia',
        'bairros': [
            'Presidente Roosevelt', 'Flamboyant', 'Martins', 'Marta Helena',
            'Santa Rosa', 'Jardim Brasília', 'Minas Gerais', 'São José',
            'Pacaembu', 'Distrito Industrial',
        ],
    },
]
# Bairros do Centro (Centro, Cazeca, Brasil, Osvaldo Rezende, Saraiva,
# Vigilato Pereira, Patrimônio, Nossa Senhora Aparecida, Santa Maria) ficam
# de fora de propósito: não existe guia de região para eles. Continuam
# aparecendo no catálogo completo, só não entram no filtro por zona.
#
# A divisão segue os quatro guias do marcotulio.pro onde eles são explícitos,
# e a geografia da cidade no resto. Corrigir um bairro é mover uma string.


# --------------------------------------------------------------------------
# utilitários

def esc(t):
    """Escapa para dentro de atributo e de texto ao mesmo tempo."""
    return (str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def brl(v):
    return 'R$ ' + format(int(v), ',d').replace(',', '.')


def zap(msg):
    from urllib.parse import quote
    return 'https://wa.me/%s?text=%s' % (ZAP, quote(msg))


def plural(n, um, muitos):
    return '%d %s' % (n, um if n == 1 else muitos)


def cortar(t, n):
    """Corta no espaço anterior ao limite: frase truncada no meio da palavra
       fica pior do que frase mais curta."""
    t = ' '.join(t.split())
    if len(t) <= n:
        return t
    return t[:t.rfind(' ', 0, n)].rstrip(' ,.;—-') + '…'


def caracteristicas(p):
    """Quartos / vagas / área, só o que estiver preenchido.

    'areaTexto' existe para lançamento, que raramente tem uma metragem só.
    Escrever 78 m² quando a planta vai de 42 a 78 não é arredondar: é dizer
    outra coisa, e quem chega esperando 78 se frustra na primeira conversa.
    """
    f = []
    if p.get('quartos'):
        f.append(plural(p['quartos'], 'quarto', 'quartos'))
    if p.get('vagas'):
        f.append(plural(p['vagas'], 'vaga', 'vagas'))
    if p.get('areaTexto'):
        f.append(p['areaTexto'])
    elif p.get('area'):
        f.append('%g m²' % p['area'])
    return f


def url_imovel(p):
    return '%s/imovel/%s/' % (SITE, p['slug'])


def foto(p, arquivo):
    return 'img/imoveis/%s/%s' % (p.get('dir', p['slug']), arquivo)


def substituir(texto, marcador, novo, arquivo):
    """Troca o miolo entre <!-- @gerado:x --> e <!-- @/gerado -->."""
    for abre, fecha in (('<!-- @gerado:%s -->', '<!-- @/gerado -->'),
                        ('/* @gerado:%s */', '/* @/gerado */')):
        a = abre % marcador
        if a in texto:
            i = texto.index(a) + len(a)
            j = texto.find(fecha, i)
            if j == -1:
                sys.exit('ERRO: %s tem "%s" mas não tem o fechamento "%s".'
                         % (arquivo, a, fecha))
            return texto[:i] + novo + texto[j:]
    sys.exit('ERRO: marcador "@gerado:%s" não encontrado em %s.' % (marcador, arquivo))


# --------------------------------------------------------------------------
# cards estáticos — o que o rastreador lê sem executar JavaScript

def card_html(p, classe):
    """Um card, com o mesmo desenho que o JS produz ao filtrar — se o card
    mudasse de forma depois de um filtro, a página pareceria quebrada."""
    cls = 'imovel' + (' ' + classe if classe else '') + (' teaser' if p.get('teaser') else '')
    # 'destaque' tira o card da fileira: ele ocupa a largura toda, em duas
    # colunas, e é o único que mostra a descrição. Um por seção — dois
    # destaques lado a lado deixam de ser destaque.
    if p.get('destaque'):
        cls += ' destaque'
    destino = p.get('link') or (url_imovel(p) if p.get('slug') else
                                zap('Quero saber mais sobre: %s — %s.' % (p['titulo'], p['local'])))
    externo = destino.startswith('http') and 'imoveis.marcotulio.pro' not in destino
    alvo = ' target="_blank" rel="noopener"' if externo else ''

    l = ['<a class="%s" href="%s"%s>' % (cls, esc(destino), alvo)]
    if p.get('img'):
        l.append('<img src="%s" alt="%s" loading="lazy" decoding="async" width="900" height="600">'
                 % (esc(p['img']), esc('%s — %s' % (p['titulo'], p['local']))))
    l.append('<div class="imovel-body">')
    l.append('<span class="selo">%s</span>' % esc(p.get('selo') or 'Disponível'))
    l.append('<h3>%s</h3>' % esc(p['titulo']))
    if p.get('construtora'):
        l.append('<div class="construtora">%s</div>' % esc(p['construtora']))
    l.append('<div class="local">📍 %s</div>' % esc(p['local']))
    if p.get('teaser') and not p.get('preco'):
        l.append('<div class="em-breve">%s</div>'
                 % esc(p.get('avisoTeaser') or 'Valores e plantas em breve'))
    if p.get('preco'):
        de = '<small> a partir de</small>' if p.get('precoDe') else ''
        l.append('<div class="preco">%s%s</div>' % (de, brl(p['preco'])))
        # pré-lançamento divulga número antes de existir tabela. Mostrar o
        # valor sem dizer isso transforma referência em promessa.
        if p.get('notaPreco'):
            l.append('<div class="preco-nota">%s</div>' % esc(p['notaPreco']))
    f = caracteristicas(p)
    if f:
        l.append('<div class="feats">%s</div>' % ''.join('<span>%s</span>' % esc(t) for t in f))
    # Só o destaque mostra a descrição: no card normal ela dobraria a altura
    # e quebraria o alinhamento da grade.
    if p.get('destaque') and p.get('desc'):
        l.append('<p class="imovel-desc">%s</p>' % esc(p['desc']))
    if p.get('slug'):
        l.append('<div class="ver-fotos">Ver o imóvel e as %d fotos →</div>' % len(p.get('fotos') or []))
    elif p.get('fotos'):
        l.append('<div class="ver-fotos">Ver %d fotos →</div>' % len(p['fotos']))
    elif p.get('link'):
        l.append('<div class="ver-guia">%s</div>'
                 % ('Entrar na lista de prioridade →' if p.get('teaser') else 'Ver o guia completo →'))
    l.append('</div></a>')
    return '\n        '.join(l)


def cards(lista, classe):
    if not lista:
        return ''
    return '\n        ' + '\n        '.join(card_html(p, classe) for p in lista) + '\n      '


def ordenar_lancamentos(lista):
    """Destaque primeiro, depois quem tem preço (do menor ao maior), e por
    último quem ainda não tem tabela. Sem isso, a ordem do JSON vira a ordem
    da página e o que entrou por último aparece no fim, mesmo sendo o mais
    relevante."""
    def chave(p):
        return (0 if p.get('destaque') else 1,
                0 if p.get('preco') else 1,
                p.get('preco') or 0)
    return sorted(lista, key=chave)


# --------------------------------------------------------------------------
# schema.org — estático, no <head>, e não mais criado por JS
#
# RealEstateListing é o tipo certo para anúncio de imóvel; Accommodation
# descreve o lugar. Um anúncio é as duas coisas, então o item sai com os dois
# e o Google escolhe o que entende.

def schema_imovel(p, com_url):
    d = {
        '@type': ['RealEstateListing', 'Accommodation'],
        'name': p['titulo'],
        'address': {
            '@type': 'PostalAddress',
            'addressLocality': 'Uberlândia',
            'addressRegion': 'MG',
            'addressCountry': 'BR',
            'streetAddress': p['local'],
        },
    }
    if com_url and p.get('slug'):
        d['url'] = url_imovel(p)
    elif p.get('link'):
        d['url'] = p['link']
    if p.get('desc'):
        d['description'] = p['desc']
    if p.get('img'):
        d['image'] = p['img'] if p['img'].startswith('http') else SITE + '/' + p['img']
    if p.get('quartos'):
        d['numberOfRooms'] = p['quartos']
    if p.get('area'):
        d['floorSize'] = {'@type': 'QuantitativeValue', 'value': p['area'], 'unitCode': 'MTK'}
    if p.get('preco'):
        d['offers'] = {
            '@type': 'Offer',
            'price': p['preco'],
            'priceCurrency': 'BRL',
            'availability': 'https://schema.org/InStock',
            'seller': {
                '@type': 'RealEstateAgent',
                'name': 'Marco Túlio Andrade — Corretor de Imóveis',
                'url': SITE + '/',
            },
        }
    return d


def schema_lista(meus, lancamentos):
    todos = [(p, True) for p in meus] + [(p, False) for p in lancamentos]
    itens = [{'@type': 'ListItem', 'position': i + 1, 'item': schema_imovel(p, own)}
             for i, (p, own) in enumerate(todos)]
    return {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'name': 'Imóveis à venda em Uberlândia',
        'numberOfItems': len(itens),
        'itemListElement': itens,
    }


def bloco_json(dado, indent=2):
    txt = json.dumps(dado, ensure_ascii=False, indent=indent)
    return ('\n  <script type="application/ld+json">\n  %s\n  </script>\n  '
            % txt.replace('\n', '\n  '))


# --------------------------------------------------------------------------
# FAQ
#
# As perguntas saem do relatório de termos de pesquisa do Google Ads, na
# língua em que as pessoas digitam. O que a campanha comprou em agosto/2026,
# em 473 impressões, foi quase tudo dúvida sobre o Minha Casa Minha Vida:
# faixa de renda (~38 impressões), quanto de subsídio (~19), quem tem direito
# (~19), lista de contemplados (~11) e teto do imóvel (~9). Nenhuma das cinco
# perguntas que estavam aqui antes respondia a qualquer uma delas.
#
# Cada resposta fecha o assunto e manda para o guia completo no marcotulio.pro,
# que é onde a resposta longa mora.

def secao_faq(faq):
    l = []
    for q in faq:
        guia = ''
        if q.get('guia'):
            guia = ('\n            <a class="faq-guia" href="%s" target="_blank" rel="noopener">%s ↗</a>'
                    % (esc(q['guia']), esc(q.get('guiaTexto') or 'Ver o guia completo')))
        l.append('<details class="faq-item">\n'
                 '          <summary>%s</summary>\n'
                 '          <div class="resp">%s%s</div>\n'
                 '        </details>' % (esc(q['p']), esc(q['r']), guia))
    return '\n        ' + '\n        '.join(l) + '\n      '


def schema_faq(faq):
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{
            '@type': 'Question',
            'name': q['p'],
            'acceptedAnswer': {'@type': 'Answer', 'text': q['r']},
        } for q in faq],
    }


# --------------------------------------------------------------------------
# seção das quatro regiões

def secao_regioes(bairros_no_catalogo):
    l = []
    for r in REGIOES:
        presentes = [b for b in r['bairros'] if b in bairros_no_catalogo]
        n = sum(bairros_no_catalogo.get(b, 0) for b in r['bairros'])
        # Mostra os bairros que realmente têm imóvel; se não houver nenhum,
        # mostra os principais mesmo assim — a região não deixa de existir.
        rotulos = presentes[:5] or r['bairros'][:4]
        l.append(
            '<div class="regiao" data-zona="%s">\n'
            '          <h3>%s</h3>\n'
            '          <p class="regiao-resumo">%s</p>\n'
            '          <p class="regiao-bairros">%s</p>\n'
            '          <button type="button" class="regiao-btn" data-zona="%s">'
            'Ver %s no catálogo</button>\n'
            '          <a class="regiao-guia" href="%s" target="_blank" rel="noopener">'
            'Guia completo da %s ↗</a>\n'
            '        </div>' % (
                r['id'], esc(r['nome']), esc(r['resumo']),
                esc(' · '.join(rotulos)), r['id'],
                plural(n, 'imóvel', 'imóveis') if n else 'os imóveis',
                esc(r['guia']), esc(r['nome'].lower())))
    return '\n        ' + '\n        '.join(l) + '\n      '


def mapa_zonas_js():
    """Bairro -> zona, para o filtro no navegador."""
    m = {}
    for r in REGIOES:
        for b in r['bairros']:
            m[b] = r['id']
    return 'var ZONAS = ' + json.dumps(m, ensure_ascii=False, indent=8, sort_keys=True) + ';'


# --------------------------------------------------------------------------
# página individual do imóvel

def pagina_imovel(p, vizinhos):
    from urllib.parse import quote
    url = url_imovel(p)
    capa = SITE + '/' + foto(p, 'og.jpg')
    fotos = p.get('fotos') or []
    regiao = next((r for r in REGIOES if r['id'] == p.get('zona')), None)

    f = caracteristicas(p)
    descricao = p.get('resumo') or p.get('desc') or ''

    # O Google corta o título por volta de 60 caracteres e a descrição por
    # volta de 158. Escrever mais do que isso não é mais informação: é
    # reticências. Os dois têm campo de override no JSON quando a fórmula
    # não servir.
    titulo_seo = p.get('tituloSeo') or ' '.join(x for x in [
        p['tipo'],
        '%g m²,' % p['area'] if p.get('area') else '',
        plural(p['quartos'], 'quarto', 'quartos') if p.get('quartos') else '',
        'em ' + p['bairro'],
        '— ' + brl(p['preco']) if p.get('preco') else '',
    ] if x)
    # Bairro e preço vêm na frente de propósito: se o Google cortar, ele corta
    # a cauda descritiva, nunca o que a pessoa está procurando saber.
    descricao_meta = p.get('metaDesc') or cortar(
        '%s, Uberlândia%s. %s' % (
            p['bairro'],
            ' · ' + brl(p['preco']) if p.get('preco') else '',
            p.get('desc') or ''), 158)

    msg = 'Vi o %s em %s no site (%s). Ainda está disponível?' % (
        p['titulo'].lower(), p['local'], url)

    # ---- schema: o anúncio, a trilha e o corretor
    dados = [schema_imovel(p, True)]
    dados[0]['photo'] = [SITE + '/' + foto(p, a) for a, _ in fotos]
    trilha = {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Imóveis em Uberlândia', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': p['bairro'], 'item': url},
            {'@type': 'ListItem', 'position': 3, 'name': p['titulo']},
        ],
    }
    dados[0]['@context'] = 'https://schema.org'

    galeria = '\n'.join(
        '      <button type="button" class="mini" data-i="%d">'
        '<img src="../../%s" alt="%s" loading="%s" decoding="async"></button>'
        % (i, foto(p, a), esc(leg), 'eager' if i < 3 else 'lazy')
        for i, (a, leg) in enumerate(fotos))

    def lista_ul(chave, titulo):
        if not p.get(chave):
            return ''
        return ('    <section class="bloco">\n      <h2>%s</h2>\n      <ul class="checks">\n%s\n'
                '      </ul>\n    </section>\n' % (
                    titulo, '\n'.join('        <li>%s</li>' % esc(x) for x in p[chave])))

    # ---- nota da avaliação da Caixa: é diferença de dinheiro real na entrada
    nota_caixa = ''
    if p.get('avaliacaoCaixa') and p.get('preco'):
        dif = p['preco'] - p['avaliacaoCaixa']
        nota_caixa = (
            '      <div class="aviso">\n'
            '        <strong>A Caixa avaliou este imóvel em %s.</strong>\n'
            '        O financiamento é calculado sobre a avaliação, não sobre o pedido. Na prática,\n'
            '        a diferença de %s entra na sua entrada — e é exatamente aí que existe espaço\n'
            '        para negociar. Prefiro te contar isso agora a você descobrir depois da proposta.\n'
            '      </div>\n' % (brl(p['avaliacaoCaixa']), brl(dif)))

    outros = ''
    if vizinhos:
        cards_v = '\n'.join(
            '        <a class="outro" href="../%s/">\n'
            '          <img src="../../%s" alt="%s" loading="lazy" decoding="async">\n'
            '          <span class="outro-txt"><strong>%s</strong><span>%s</span>%s</span>\n'
            '        </a>' % (
                v['slug'], foto(v, 'capa.jpg'), esc(v['titulo']), esc(v['titulo']),
                esc(v['local']), '<span class="outro-preco">%s</span>' % brl(v['preco'])
                if v.get('preco') else '')
            for v in vizinhos)
        outros = ('    <section class="bloco">\n      <h2>Outros imóveis da minha carteira</h2>\n'
                  '      <div class="outros">\n%s\n      </div>\n    </section>\n' % cards_v)

    contexto = ''
    if regiao:
        contexto = (
            '    <section class="bloco">\n'
            '      <h2>Onde fica</h2>\n'
            '      <p>%s fica na <strong>%s</strong> de Uberlândia%s. %s</p>\n'
            '      <p><a class="link-guia" href="%s" target="_blank" rel="noopener">'
            'Ver o guia completo da %s, com todos os lançamentos da região ↗</a></p>\n'
            '    </section>\n' % (
                esc(p['bairro']), esc(regiao['nome'].lower()),
                ', ' + esc(p['referencia']) if p.get('referencia') else '',
                esc(regiao['resumo']), esc(regiao['guia']), esc(regiao['nome'].lower())))

    cond = ''
    if p.get('condominio'):
        cond = '<p class="cond">Condomínio <strong>%s</strong></p>' % esc(p['condominio'])

    return TEMPLATE_IMOVEL.format(
        titulo_seo=esc(titulo_seo),
        descricao_meta=esc(descricao_meta),
        url=url, capa=capa, slug=p['slug'],
        alt_capa=esc('%s — %s' % (p['titulo'], p['local'])),
        h1=esc(p.get('h1') or p['titulo']),
        local=esc(p['local']),
        cond=cond,
        selo=esc(p['selo']),
        preco=brl(p['preco']) if p.get('preco') else 'Valor sob consulta',
        feats=''.join('<span>%s</span>' % esc(t) for t in f),
        nota_caixa=nota_caixa,
        resumo=esc(descricao),
        galeria=galeria,
        n_fotos=len(fotos),
        itens=lista_ul('itens', 'O que tem dentro'),
        lazer=lista_ul('lazer', 'O condomínio'),
        contexto=contexto,
        outros=outros,
        zap=esc(zap(msg)),
        zap_visita=esc(zap('Quero agendar uma visita ao %s em %s.' % (p['titulo'].lower(), p['bairro']))),
        json_imovel=json.dumps(dados[0], ensure_ascii=False, indent=2).replace('\n', '\n  '),
        json_trilha=json.dumps(trilha, ensure_ascii=False, indent=2).replace('\n', '\n  '),
    )


TEMPLATE_IMOVEL = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo_seo}</title>
  <meta name="description" content="{descricao_meta}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta name="theme-color" content="#1A56DB">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%231A56DB'/%3E%3Ctext x='32' y='43' font-family='Helvetica,Arial,sans-serif' font-size='30' font-weight='bold' fill='%23fff' text-anchor='middle'%3EMT%3C/text%3E%3C/svg%3E">

  <meta property="og:type" content="article">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{titulo_seo}">
  <meta property="og:description" content="{descricao_meta}">
  <meta property="og:image" content="{capa}">
  <meta property="og:image:secure_url" content="{capa}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{alt_capa}">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:site_name" content="Marco Túlio Imóveis">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{titulo_seo}">
  <meta name="twitter:description" content="{descricao_meta}">
  <meta name="twitter:image" content="{capa}">

  <meta name="geo.region" content="BR-MG">
  <meta name="geo.placename" content="Uberlândia">

  <script type="application/ld+json">
  {json_imovel}
  </script>
  <script type="application/ld+json">
  {json_trilha}
  </script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">

  <style>
    :root {{
      --azul:#1A56DB; --azul-profundo:#11399E; --azul-claro:#EAF1FE;
      --coral:#FF5A2C; --coral-fundo:#FFEDE5; --coral-profundo:#C8390F;
      --tinta:#0F1B2D; --tinta-suave:#41506A; --nevoa:#D9E1EE;
      --fundo:#F7F9FC; --superficie:#FFFFFF;
      --zap:#0E7A33; --zap-escuro:#0A5526;
      --fdisp:'Bricolage Grotesque',system-ui,sans-serif;
      --fbody:'Hanken Grotesk',system-ui,sans-serif;
      --maxw:1000px;
    }}
    *,*::before,*::after {{ box-sizing:border-box; }}
    body {{
      margin:0; background:var(--fundo); color:var(--tinta);
      font-family:var(--fbody); font-size:18px; line-height:1.65;
      -webkit-font-smoothing:antialiased;
    }}
    img {{ max-width:100%; display:block; }}
    a {{ color:var(--azul); }}
    .wrap {{ max-width:var(--maxw); margin:0 auto; padding:0 20px; }}

    .topo {{
      position:sticky; top:0; z-index:40; background:rgba(255,255,255,.92);
      backdrop-filter:blur(10px); border-bottom:1px solid var(--nevoa);
    }}
    .topo-in {{
      max-width:var(--maxw); margin:0 auto; padding:12px 20px;
      display:flex; align-items:center; justify-content:space-between; gap:16px;
    }}
    .marca {{ font-family:var(--fdisp); font-weight:800; font-size:19px; color:var(--tinta); text-decoration:none; }}
    .marca span {{ color:var(--azul); }}
    .topo-zap {{
      background:var(--zap); color:#fff; text-decoration:none; font-weight:600;
      padding:9px 18px; border-radius:999px; font-size:15px; white-space:nowrap;
    }}
    .topo-zap:hover {{ background:var(--zap-escuro); }}

    .trilha {{ font-size:14px; color:var(--tinta-suave); padding:18px 0 0; }}
    .trilha a {{ color:var(--tinta-suave); }}
    .trilha b {{ color:var(--tinta); font-weight:600; }}

    .capa {{ padding:20px 0 8px; }}
    .selo {{
      display:inline-block; background:var(--azul-claro); color:var(--azul-profundo);
      font-weight:700; font-size:13px; letter-spacing:.04em; text-transform:uppercase;
      padding:6px 13px; border-radius:999px;
    }}
    h1 {{
      font-family:var(--fdisp); font-weight:800; line-height:1.1;
      font-size:clamp(30px,4.6vw,46px); margin:14px 0 8px; letter-spacing:-.02em;
    }}
    .endereco {{ color:var(--tinta-suave); font-size:19px; margin:0; }}
    .cond {{ color:var(--tinta-suave); font-size:17px; margin:4px 0 0; }}

    .preco-caixa {{
      display:flex; flex-wrap:wrap; align-items:center; gap:12px 28px;
      background:var(--superficie); border:1px solid var(--nevoa);
      border-radius:18px; padding:22px 24px; margin:22px 0;
    }}
    .preco {{ font-family:var(--fdisp); font-weight:800; font-size:clamp(30px,4vw,40px); letter-spacing:-.02em; }}
    .feats {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .feats span {{
      background:var(--fundo); border:1px solid var(--nevoa); border-radius:999px;
      padding:6px 15px; font-size:15px; font-weight:600; color:var(--tinta-suave);
    }}
    .aviso {{
      background:var(--coral-fundo); border-left:4px solid var(--coral);
      border-radius:0 14px 14px 0; padding:18px 22px; margin:0 0 24px; font-size:17px;
    }}
    .aviso strong {{ color:var(--coral-profundo); }}

    .chamada {{ display:flex; flex-wrap:wrap; gap:12px; margin:24px 0 8px; }}
    .btn {{
      display:inline-block; text-decoration:none; font-weight:700; font-size:17px;
      padding:15px 28px; border-radius:999px; border:2px solid transparent;
    }}
    .btn-zap {{ background:var(--zap); color:#fff; }}
    .btn-zap:hover {{ background:var(--zap-escuro); }}
    .btn-linha {{ border-color:var(--nevoa); color:var(--tinta); background:var(--superficie); }}
    .btn-linha:hover {{ border-color:var(--azul); color:var(--azul); }}

    .galeria {{
      display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr));
      gap:10px; margin:10px 0 6px;
    }}
    .mini {{
      padding:0; border:0; background:none; cursor:pointer; border-radius:12px;
      overflow:hidden; aspect-ratio:4/3; line-height:0;
    }}
    .mini img {{ width:100%; height:100%; object-fit:cover; transition:transform .3s; }}
    .mini:hover img {{ transform:scale(1.05); }}
    .mini:focus-visible {{ outline:3px solid var(--azul); outline-offset:3px; }}

    .bloco {{ margin:44px 0; }}
    h2 {{
      font-family:var(--fdisp); font-weight:800; font-size:clamp(23px,3vw,30px);
      letter-spacing:-.02em; margin:0 0 16px;
    }}
    .checks {{ list-style:none; padding:0; margin:0; display:grid; gap:10px;
      grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); }}
    .checks li {{ position:relative; padding-left:30px; }}
    .checks li::before {{
      content:''; position:absolute; left:0; top:.55em; width:16px; height:9px;
      border-left:3px solid var(--azul); border-bottom:3px solid var(--azul);
      transform:rotate(-45deg);
    }}
    .link-guia {{ font-weight:600; }}

    /* auto-fill, e não auto-fit: com um único imóvel na carteira, auto-fit
       colapsa as trilhas vazias e o card estica para a largura inteira —
       uma foto de 3:2 vira um bloco de 660px de altura. */
    .outros {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); }}
    .outro {{
      display:block; background:var(--superficie); border:1px solid var(--nevoa);
      border-radius:16px; overflow:hidden; text-decoration:none; color:inherit;
    }}
    .outro:hover {{ border-color:var(--azul); }}
    .outro img {{ width:100%; aspect-ratio:3/2; object-fit:cover; }}
    .outro-txt {{ display:block; padding:16px 18px; }}
    .outro-txt strong {{ display:block; font-family:var(--fdisp); font-size:19px; }}
    .outro-txt > span {{ display:block; color:var(--tinta-suave); font-size:15px; }}
    .outro-preco {{ color:var(--azul); font-weight:700; margin-top:6px; }}

    .fecha {{
      background:var(--tinta); color:#fff; border-radius:22px;
      padding:clamp(30px,5vw,48px); margin:52px 0;
    }}
    .fecha h2 {{ color:#fff; }}
    .fecha p {{ color:#C6D0E2; max-width:56ch; }}

    footer {{ padding:36px 0 60px; font-size:15px; color:var(--tinta-suave); }}
    footer a {{ color:var(--tinta-suave); }}

    dialog {{
      border:0; padding:0; background:none; max-width:96vw; max-height:96vh;
      margin:auto; overflow:visible;
    }}
    dialog::backdrop {{ background:rgba(9,14,28,.85); }}
    .lb {{ position:relative; }}
    .lb img {{
      max-width:96vw; max-height:80vh; width:auto; border-radius:12px;
      background:#000; margin:0 auto;
    }}
    .lb-leg {{ color:#fff; text-align:center; padding:12px 8px 0; font-size:16px; }}
    .lb-bt {{
      position:absolute; top:50%; transform:translateY(-50%); background:rgba(255,255,255,.94);
      border:0; width:46px; height:46px; border-radius:50%; font-size:24px; cursor:pointer;
      color:var(--tinta); line-height:1;
    }}
    .lb-ant {{ left:-8px; }} .lb-prox {{ right:-8px; }}
    .lb-fechar {{
      position:absolute; top:-46px; right:0; background:none; border:0; color:#fff;
      font-size:34px; cursor:pointer; line-height:1;
    }}
    @media (max-width:640px) {{
      body {{ font-size:17px; }}
      .lb-ant {{ left:2px; }} .lb-prox {{ right:2px; }}
      .lb img {{ max-height:66vh; }}
    }}
    @media (prefers-reduced-motion:reduce) {{
      * {{ animation:none !important; transition:none !important; }}
    }}
  </style>
</head>
<body>

<header class="topo">
  <div class="topo-in">
    <a class="marca" href="/">marco túlio <span>imóveis</span></a>
    <a class="topo-zap" href="{zap}" target="_blank" rel="noopener">Falar comigo</a>
  </div>
</header>

<main class="wrap">
  <nav class="trilha" aria-label="Trilha de navegação">
    <a href="/">Imóveis em Uberlândia</a> › <b>{local}</b>
  </nav>

  <div class="capa">
    <span class="selo">{selo}</span>
    <h1>{h1}</h1>
    <p class="endereco">📍 {local}</p>
    {cond}
  </div>

  <div class="preco-caixa">
    <div class="preco">{preco}</div>
    <div class="feats">{feats}</div>
  </div>
{nota_caixa}
  <p class="resumo">{resumo}</p>

  <div class="chamada">
    <a class="btn btn-zap" href="{zap_visita}" target="_blank" rel="noopener">Agendar uma visita</a>
    <a class="btn btn-linha" href="https://simulador.marcotulio.pro/" target="_blank" rel="noopener">Simular o financiamento</a>
  </div>

  <section class="bloco">
    <h2>As {n_fotos} fotos</h2>
    <div class="galeria">
{galeria}
    </div>
  </section>

{itens}{lazer}{contexto}
  <section class="fecha">
    <h2>Quer ver por dentro?</h2>
    <p>Eu marco a visita, levo você e cuido do financiamento do começo ao fim — simulação,
       documentação, aprovação e assinatura. Sem custo para quem compra.</p>
    <div class="chamada">
      <a class="btn btn-zap" href="{zap}" target="_blank" rel="noopener">Chamar no WhatsApp</a>
    </div>
  </section>

{outros}
  <footer>
    <p><strong>Marco Túlio Andrade Freitas</strong> — corretor parceiro da Torrano Negócios
       Imobiliários, CRECI/MG 7469 · CNPJ 51.647.689/0001-81</p>
    <p><a href="/">Ver todos os imóveis</a> ·
       <a href="https://www.marcotulio.pro" target="_blank" rel="noopener">marcotulio.pro ↗</a></p>
  </footer>
</main>

<dialog id="lb" aria-label="Fotos do imóvel">
  <div class="lb">
    <button class="lb-fechar" id="lbFechar" aria-label="Fechar">&times;</button>
    <button class="lb-bt lb-ant" id="lbAnt" aria-label="Foto anterior">‹</button>
    <img id="lbImg" alt="">
    <button class="lb-bt lb-prox" id="lbProx" aria-label="Próxima foto">›</button>
    <p class="lb-leg" id="lbLeg"></p>
  </div>
</dialog>

<script>
/* Lightbox. O <dialog> nativo já entrega ESC e prisão de foco de graça.
   As miniaturas são <button>: sem JS a página continua inteira e legível. */
(function () {{
  var dlg = document.getElementById('lb');
  if (!dlg || !dlg.showModal) {{ return; }}
  var minis = [].slice.call(document.querySelectorAll('.mini'));
  var img = document.getElementById('lbImg');
  var leg = document.getElementById('lbLeg');
  var i = 0;

  function abre(n) {{
    i = (n + minis.length) % minis.length;
    var m = minis[i].querySelector('img');
    img.src = m.src;
    img.alt = m.alt;
    leg.textContent = m.alt + '  ·  ' + (i + 1) + '/' + minis.length;
    if (!dlg.open) {{ dlg.showModal(); }}
  }}

  minis.forEach(function (b, n) {{ b.addEventListener('click', function () {{ abre(n); }}); }});
  document.getElementById('lbAnt').addEventListener('click', function () {{ abre(i - 1); }});
  document.getElementById('lbProx').addEventListener('click', function () {{ abre(i + 1); }});
  document.getElementById('lbFechar').addEventListener('click', function () {{ dlg.close(); }});
  dlg.addEventListener('keydown', function (e) {{
    if (e.key === 'ArrowRight') {{ abre(i + 1); }}
    if (e.key === 'ArrowLeft') {{ abre(i - 1); }}
  }});
  /* clique no fundo fecha */
  dlg.addEventListener('click', function (e) {{ if (e.target === dlg) {{ dlg.close(); }} }});
}})();
</script>
</body>
</html>
'''


# --------------------------------------------------------------------------

def main():
    os.chdir(RAIZ)
    meus = json.load(open('dados/imoveis.json', encoding='utf-8'))
    lancamentos = json.load(open('dados/lancamentos.json', encoding='utf-8'))
    faq = json.load(open('dados/faq.json', encoding='utf-8'))
    torrano = json.load(open('dados/torrano.json', encoding='utf-8'))

    # A capa de cada imóvel próprio é sempre capa.jpg da pasta dele. O link do
    # card é relativo de propósito: assim a página abre igual em produção, em
    # pré-visualização do Netlify e num servidor local. Absoluto só onde tem
    # que ser — canonical, og:url, schema.org e sitemap.
    for p in meus:
        p['img'] = foto(p, 'capa.jpg')
        p['link'] = 'imovel/%s/' % p['slug']

    html = open('index.html', encoding='utf-8').read()

    # 1. cards no HTML, legíveis sem JavaScript
    html = substituir(html, 'cards-meus', cards(meus, ''), 'index.html')
    html = substituir(html, 'cards-lancamentos',
                      cards(ordenar_lancamentos(lancamentos), 'lancamento'), 'index.html')
    html = substituir(html, 'cards-torrano', cards(torrano, 'torrano'), 'index.html')

    # 2. as quatro regiões
    bairros = {}
    for m in re.finditer(r"bairro:'([^']+)'", html):
        bairros[m.group(1)] = bairros.get(m.group(1), 0) + 1
    for p in meus + lancamentos + torrano:
        b = p.get('bairro')
        if b:
            bairros[b] = bairros.get(b, 0) + 1
    html = substituir(html, 'regioes', secao_regioes(bairros), 'index.html')

    # 3. FAQ: a lista visível e o schema saem da mesma fonte, para não
    #    divergirem — o Google trata schema que não confere com a página
    #    como motivo para ignorar o rich result inteiro.
    html = substituir(html, 'faq', secao_faq(faq), 'index.html')
    html = substituir(html, 'schema',
                      bloco_json(schema_lista(meus, lancamentos))
                      + bloco_json(schema_faq(faq)).rstrip(' '), 'index.html')

    # 4. os mesmos dados para busca, filtro e galeria no navegador
    dados_js = (
        '\n      var MEUS_IMOVEIS = %s;\n'
        '      var LANCAMENTOS = %s;\n'
        '      var TORRANO = %s;\n'
        '      %s\n      ' % (
            json.dumps(meus, ensure_ascii=False, indent=8).replace('\n', '\n      '),
            json.dumps(ordenar_lancamentos(lancamentos), ensure_ascii=False, indent=8).replace('\n', '\n      '),
            json.dumps(torrano, ensure_ascii=False, indent=8).replace('\n', '\n      '),
            mapa_zonas_js().replace('\n', '\n      ')))
    html = substituir(html, 'dados', dados_js, 'index.html')

    open('index.html', 'w', encoding='utf-8').write(html)

    # 5. uma página por imóvel
    for p in meus:
        pasta = os.path.join('imovel', p['slug'])
        os.makedirs(pasta, exist_ok=True)
        vizinhos = [v for v in meus if v['slug'] != p['slug']]
        open(os.path.join(pasta, 'index.html'), 'w', encoding='utf-8') \
            .write(pagina_imovel(p, vizinhos))

    # 6. sitemap
    urls = [(SITE + '/', '1.0', 'weekly')]
    urls += [(url_imovel(p), '0.9', 'monthly') for p in meus]
    corpo = '\n'.join(
        '  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n'
        '    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n  </url>'
        % (u, HOJE, freq, pri) for u, pri, freq in urls)
    open('sitemap.xml', 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % corpo)

    print('imóveis próprios : %d  (%d páginas geradas)' % (len(meus), len(meus)))
    print('lançamentos      : %d' % len(lancamentos))
    print('exclusivos Torrano: %d' % len(torrano))
    print('bairros no mapa  : %d de %d com imóvel no catálogo'
          % (sum(1 for b in bairros if any(b in r['bairros'] for r in REGIOES)), len(bairros)))
    print('perguntas na FAQ : %d  (%d com guia no marcotulio.pro)'
          % (len(faq), sum(1 for q in faq if q.get('guia'))))
    print('URLs no sitemap  : %d  (lastmod %s)' % (len(urls), HOJE))


if __name__ == '__main__':
    main()
