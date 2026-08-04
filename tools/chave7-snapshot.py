#!/usr/bin/env python3
"""
Recorte temporário do catálogo do portal parceiro Chave7.

PONTE, NÃO SOLUÇÃO. Quando a API-Key de integração do Chave7 chegar, este
script sai de cena e entra a ingestão oficial:

    GET https://integracao.chave7.com.br/api/v1/ingest-file
        header: x-api-key: <sua chave>
    -> feed XML no padrão VRSync (o mesmo de VivaReal / ZAP / OLX)

A API traz dados sempre atuais, é sancionada e não quebra quando o layout do
site deles muda. Endpoints úteis da mesma API:
    GET  /api/v1/config                  filtros ativos da sua integração
    GET  /api/v1/property/{listingId}    imóvel individual (XML ou ?format=json)
    POST /api/v1/url                     registra sua URL de webhook
    GET  /api/v1/logs                    logs de entrega dos webhooks

ATENÇÃO: a documentação deles diz que a API-Key NUNCA pode ser exposta do lado
do cliente. Como o site é estático, a chave tem que ficar em GitHub Secrets e a
ingestão rodar no build — nunca dentro do index.html.

--------------------------------------------------------------------------------
O que ESTE script faz, enquanto a chave não chega:

1. Você baixa as páginas de busca amplas que estão no sitemap.xml do Chave7.
   O robots.txt deles permite /buscar-imoveis; a /api/ é PROIBIDA e não é usada
   aqui. Use pausa entre as requisições para não pesar no servidor deles:

       curl -A "Mozilla/5.0" "<url de busca>" -o p1.html
       sleep 3
       curl -A "Mozilla/5.0" "<outra url>"   -o p2.html

2. Roda este script na pasta onde estão os p*.html:

       python3 chave7-snapshot.py

3. Ele extrai o JSON estruturado que o Next.js embute na própria página
   (commercialId, price, neighborhood, bedrooms, bathrooms, garage, usefulArea,
   landArea, coverPhotoUrl, types), o que é bem mais estável do que raspar o
   HTML renderizado. Saída: catalogo.json

4. Ao converter para o array CHAVE7 do index.html, remova o sufixo "=s0" das
   fotos: sem ele o S3 devolve a versão de 512px, com cerca de 1/3 do peso.
   (Outros parâmetros de redimensionamento, tipo "=s400", devolvem HTTP 403.)
"""

import re
import json
import glob

# Os tipos vêm em inglês no payload; aqui viram os rótulos usados nos chips
# de busca do site (Casa / Apartamento / Terreno / Comercial).
TIPO = {
    'apartment': 'Apartamento', 'flat': 'Apartamento', 'kitnet': 'Apartamento',
    'studio': 'Apartamento',
    'house': 'Casa', 'standard-house': 'Casa', 'condo-house': 'Casa',
    'townhouse': 'Casa',
    'land': 'Terreno', 'lot': 'Terreno', 'allotment': 'Terreno',
    'farm': 'Terreno', 'rural': 'Terreno',
    'commercial': 'Comercial', 'store': 'Comercial', 'office': 'Comercial',
    'shed': 'Comercial', 'warehouse': 'Comercial',
}


def objeto_em(s, i):
    """Extrai o objeto JSON que contém a posição i, balanceando as chaves.

    O payload está no flight data do React Server Components, então não há um
    JSON único para carregar: é preciso achar os limites de cada objeto.
    """
    ini = s.rfind('{', 0, i)
    while ini > 0:
        prof = 0
        for j in range(ini, min(len(s), ini + 20000)):
            if s[j] == '{':
                prof += 1
            elif s[j] == '}':
                prof -= 1
                if prof == 0:
                    try:
                        return json.loads(s[ini:j + 1])
                    except Exception:
                        break
        ini = s.rfind('{', 0, ini)
    return None


def classifica(types):
    for t in types or []:
        nome = TIPO.get((t.get('type') or '').lower())
        if nome:
            return nome
    return None


def main():
    vistos = {}
    arquivos = sorted(glob.glob('p*.html'))
    if not arquivos:
        print('Nenhum p*.html encontrado. Baixe as paginas de busca primeiro.')
        return

    for f in arquivos:
        html = open(f, encoding='utf-8', errors='replace').read()
        # o flight data vem escapado; desescapar deixa o JSON parseavel
        texto = html.replace('\\\\"', '"').replace('\\"', '"')
        for m in re.finditer(r'"commercialId":(\d+)', texto):
            o = objeto_em(texto, m.start())
            if not o or 'commercialId' not in o:
                continue
            if o.get('active') is False:
                continue
            vistos[o['commercialId']] = {
                'cod': o['commercialId'],
                'tipo': classifica(o.get('types')),
                'bairro': o.get('neighborhood'),
                'preco': o.get('price'),
                'quartos': o.get('bedrooms') or None,
                'banheiros': o.get('bathrooms') or None,
                'vagas': o.get('garage') or None,
                'areaUtil': o.get('usefulArea') or None,
                'areaTerreno': o.get('landArea') or None,
                'img': o.get('coverPhotoUrl'),
            }

    saida = sorted(vistos.values(), key=lambda r: r['cod'])
    json.dump(saida, open('catalogo.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('paginas lidas:   %d' % len(arquivos))
    print('imoveis unicos:  %d' % len(saida))
    print('gravado em:      catalogo.json')


if __name__ == '__main__':
    main()
