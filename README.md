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
dados/faq.json           perguntas e respostas (vira HTML + FAQPage schema)
dados/torrano.json       exclusivos da Torrano (o card leva ao site deles)
tools/gerar.py           gera o site a partir dos dois arquivos acima
tools/conferir.py        compara os lançamentos com as páginas do marcotulio.pro
index.html               a capa (HTML/CSS/JS em arquivo único)
imovel/<slug>/           uma página por imóvel — GERADAS, não edite à mão
img/imoveis/<pasta>/     fotos de cada imóvel
sitemap.xml              GERADO
robots.txt               diretrizes de indexação
```

## Os dois números

| onde | número | por quê |
|---|---|---|
| todo link `wa.me` | **(34) 92001-7016** | WhatsApp Business do Meta — é para onde vai toda conversa iniciada pelo site |
| links `tel:`, schema.org, texto visível | **(34) 99677-8075** | telefone padrão, para ligação e contato geral |

**Não unifique os dois.** Separar a conversa do site do telefone pessoal é o
motivo de existir a conta business: é ela que dá catálogo, respostas rápidas,
etiquetas e as métricas do Meta.

Cada número tem um lugar só no código:

- `index.html` → `var ZAP` (o JS reescreve o `href` de todo `[data-zap]`; os
  `href` escritos no HTML são o fallback para quem não executa JS, e precisam
  ser trocados junto)
- `tools/gerar.py` → `ZAP` e `FONE`, no topo do arquivo

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

## Como atualizar um lançamento

**A página do empreendimento no marcotulio.pro é a fonte.** Quando ela e a
tabela de um guia de região discordam, vale a página — é ela que está sendo
mantida. Em 16/08/2026 o guia da zona norte dizia *"a partir de R$ 252 mil"*
para o Matíz enquanto a página dele dizia *"a partir de R$ 235 mil"*.

Para descobrir o que saiu de sincronia:

```
python3 tools/conferir.py
```

Ele baixa o `link` de cada lançamento e procura o `preco` do card na página,
em duas passadas: primeiro no `<title>` e na meta description, onde costuma
estar o valor de entrada; se não houver preço ali, procura o valor exato no
corpo — é de lá que vêm os preços de quem só tem tabela por tipologia (Arsen
Sabiá, Bit 580, Vila Vert), e esses aparecem como `ok (corpo)`.

Só é divergência quando o valor do card não aparece em lugar nenhum da página.
Sai com código 1 nesse caso, e mostra a data de atualização de cada página.

O script **não escreve nada**. Depois de conferir, ajuste
`dados/lancamentos.json` à mão e rode `python3 tools/gerar.py`.

Quatro campos existem porque lançamento é diferente de imóvel pronto:

- `destaque` — tira o card da fileira: ele ocupa a largura toda, em duas
  colunas, e é o único que mostra a `desc`. Use **um por seção**; dois
  destaques lado a lado deixam de ser destaque. Hoje é o Gran Vic Essenza.

- `areaTexto` — faixa de metragem (`"42 a 78 m²"`). Lançamento raramente tem
  uma metragem só, e escrever o teto como se fosse a unidade não é arredondar:
  é dizer outra coisa, e quem chega esperando o teto se frustra na visita.
- `notaPreco` — linha pequena sob o valor. Pré-lançamento divulga número antes
  de existir tabela; mostrar o valor sem dizer isso transforma referência em
  promessa. O Gran Vic Essenza usa
  `"condição preliminar de pré-lançamento, não é tabela oficial"`.
- `avisoTeaser` — substitui *"Valores e plantas em breve"* num card `teaser`
  **sem preço**, quando o motivo de não ter valor mudou. Com `preco` definido
  ele não aparece: aí quem cumpre o papel é o `notaPreco`.

## Os exclusivos da Torrano

`dados/torrano.json` traz a captação exclusiva da imobiliária de que ele é
corretor parceiro. Cada card leva para `torrano.com.br/imovel/<id>` — o
atendimento cai no sistema deles, que é o combinado.

Os dados vêm das páginas públicas da Torrano (o `robots.txt` deles é
`Allow: /`), do JSON que o Next.js embute na própria página. O campo que
separa o que é deles do que é repasse do Chave7 é `source`: `own` = exclusivo,
`chave7` = catálogo do portal. Só os `own` entram aqui.

Dois cuidados que valem repetir na próxima atualização:

- **Título montado dos campos, não do texto livre.** O cadastro deles é
  escrito à mão e vem com "à venda", emoji e nome de condomínio no meio.
  O card usa `{tipo} de {N} quartos no {bairro}`, e os treze ficam
  consistentes entre si.
- **Deduplicar contra `dados/imoveis.json`.** O apartamento de Chácaras
  Tubalina está nos dois lugares: é captação dele, cadastrada lá também.
  Publicar o mesmo imóvel duas vezes confunde o visitante e divide o sinal
  de SEO entre duas URLs. Ele fica só em `/imovel/`, com página inteira.

**A API-Key do Chave7 não está no site da Torrano, e isso está certo.** Eles
ingerem o Chave7 no próprio backend (Supabase) e o site lê de lá; a chave vive
no servidor deles, nunca no navegador — exatamente o que a documentação do
Chave7 exige. Uma chave que desse para achar num site público seria uma falha
de segurança, não um atalho.

## Como manter a FAQ

As perguntas de `dados/faq.json` viram **duas coisas ao mesmo tempo**: a lista
visível na página e o `FAQPage` do schema.org. Saem da mesma fonte de
propósito — quando o schema não confere com o texto visível, o Google descarta
o rich result inteiro.

**Escreva a pergunta na língua em que a pessoa digita, não na sua.** As nove
atuais vieram do relatório de termos de pesquisa do Google Ads. Em agosto/2026,
473 impressões compradas foram quase todas dúvida sobre o Minha Casa Minha
Vida, nesta ordem:

| o que perguntam | impressões | pergunta na FAQ |
|---|---|---|
| faixa de renda | ~38 | Qual a faixa de renda do MCMV em 2026? |
| quem tem direito / requisitos | ~19 | Quem tem direito ao Minha Casa Minha Vida? |
| quanto de subsídio | ~19 | Quanto eu recebo de subsídio? |
| lista de contemplados | ~11 | Existe lista de contemplados em Uberlândia? |
| valor máximo do imóvel | ~9 | Qual o valor máximo do imóvel em Uberlândia? |

Nenhuma das cinco perguntas que estavam aqui antes respondia a qualquer uma
delas. Para atualizar, exporte um relatório novo em **Google Ads → Estatísticas
e relatórios → Termos de pesquisa** e me mande.

Cada resposta fecha o assunto em um parágrafo e manda para o guia completo no
marcotulio.pro (campo `guia`). O texto longo mora lá; repetir aqui faria as
duas páginas competirem.

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
