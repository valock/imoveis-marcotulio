# Imóveis Marco Túlio — Vitrine de Imóveis em Uberlândia

Vitrine de imóveis em Uberlândia: imóveis de captação própria, lançamentos de
construtoras e o catálogo do portal parceiro Chave7, com o financiamento
(Caixa, Minha Casa Minha Vida, FGTS) resolvido pelo corretor.

A **autoridade do profissional** mora no site oficial
[marcotulio.pro](https://www.marcotulio.pro) — aqui a página só apresenta o
essencial e faz a ponte para lá. Este domínio é a vertente de **catálogo + SEO**.

🔗 **Ao vivo:** https://imoveis.marcotulio.pro

## Conteúdo

```
dados/imoveis.json       fonte única dos imóveis de captação própria
dados/lancamentos.json   fonte única dos lançamentos de construtora
tools/gerar.py           gera o site a partir dos dois arquivos acima
index.html               a capa (HTML/CSS/JS em arquivo único)
imovel/<slug>/           uma página por imóvel — GERADAS, não edite à mão
img/imoveis/<pasta>/     fotos de cada imóvel
sitemap.xml              GERADO
robots.txt               diretrizes de indexação
```

## Como publicar um imóvel

**1.** Coloque as fotos em `img/imoveis/<pasta-do-imovel>/`, numeradas
(`01.jpg`, `02.jpg`, …), com no máximo 1200px no lado maior e cerca de 100 KB
cada. Mais duas:

| arquivo    | tamanho  | serve para                                  |
|------------|----------|---------------------------------------------|
| `capa.jpg` | 900×600  | o card na capa do site                      |
| `og.jpg`   | 1200×630 | a prévia do link no WhatsApp, Face, LinkedIn |

**2.** Adicione um objeto em `dados/imoveis.json`:

```json
{
  "slug":   "casa-3-quartos-santa-monica-uberlandia",
  "dir":    "santa-monica-3q",
  "selo":   "Captação exclusiva",
  "tipo":   "Casa",
  "titulo": "Casa 3 quartos com quintal",
  "h1":     "Casa de 3 quartos com quintal no Santa Mônica",
  "local":  "Santa Mônica, Uberlândia",
  "bairro": "Santa Mônica",
  "zona":   "leste",
  "preco":  480000,
  "quartos": 3, "vagas": 2, "area": 180,
  "desc":   "Casa térrea reformada, a 5 minutos da UFU.",
  "resumo": "Parágrafo mais solto, que abre a página do imóvel.",
  "itens":  ["Sala ampla", "Cozinha planejada", "Quintal com churrasqueira"],
  "fotos":  [["01.jpg", "Fachada"], ["02.jpg", "Sala"]]
}
```

Campos que valem conhecer:

- `slug` — vira a URL: `/imovel/<slug>/`. Use palavras que a pessoa digitaria
  na busca (`tipo-quartos-bairro-cidade`). **Não mude depois de publicado**:
  URL trocada é link perdido.
- `dir` — nome da pasta das fotos, quando diferente do slug.
- `zona` — `norte`, `sul`, `leste` ou `oeste`. Liga o imóvel ao guia da região
  no marcotulio.pro.
- `avaliacaoCaixa` — quando existe, a página explica sozinha a diferença entre
  o valor pedido e o avaliado, e o que isso faz com a entrada.
- `lazer` — lista das áreas comuns do condomínio (vira uma seção própria).
- `tituloSeo` e `metaDesc` — só quando a fórmula automática não servir.

**3.** Rode o gerador:

```
python3 tools/gerar.py
```

Ele reescreve, de uma vez e sem sair de sincronia:

1. os **cards em HTML** dentro do `index.html`;
2. o **schema.org** (`ItemList` de `RealEstateListing`) no `<head>`;
3. a **página do imóvel** em `/imovel/<slug>/`, com title, descrição,
   canonical, Open Graph, `RealEstateListing`, `BreadcrumbList` e galeria;
4. o **`sitemap.xml`**.

Nunca edite esses quatro à mão — a próxima execução sobrescreve.

## Por que o gerador existe

Antes, os imóveis só existiam num array JavaScript e os cards eram montados no
navegador. Quem lê a página sem executar JS — e é assim que boa parte do
rastreamento acontece — via literalmente **"Nenhum imóvel publicado ainda"**.

Medição de 16/08/2026, na página no ar: 163 KB de HTML, **11.237 caracteres de
texto indexável, nenhum deles com o nome de um imóvel**. O Search Console do
mesmo período fecha a conta: 19 impressões, 0 cliques, **1 página indexada** e
**1 consulta**, o próprio nome do corretor.

Site de uma página só tem uma chance de ranquear. Cada imóvel com URL própria
tem a sua.

## Integração com o Chave7

O catálogo do Chave7 (151 imóveis) é um **recorte capturado em 04/08/2026** das
páginas de busca do portal — o `robots.txt` deles permite `/buscar-imoveis`; a
`/api/` é proibida e não foi usada. Ver `tools/chave7-snapshot.py`.

Ele continua sendo montado pelo navegador, e isso é de propósito: são imóveis
de terceiro, que já têm página no portal deles. Publicar o mesmo texto como
conteúdo próprio criaria conteúdo duplicado com a fonte, o que atrapalha os
dois lados.

**Próximo passo:** quando a API-Key chegar, o recorte sai e entra a ingestão
oficial via feed VRSync:

```
GET https://integracao.chave7.com.br/api/v1/ingest-file
    header: x-api-key: <a chave>
```

A chave **não pode** ficar no `index.html` (site estático é código aberto na
prática). Ela vai em GitHub Secrets e a ingestão roda no build.

## Stack

Site estático. Sem build obrigatório, sem dependências de runtime. O gerador é
Python puro, da biblioteca padrão. Única externa em produção: Google Fonts
(Bricolage Grotesque + Hanken Grotesk).

## Deploy

Publicado no **Netlify**, a partir da branch `main` deste repositório.
