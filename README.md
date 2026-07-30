# Imóveis Marco Túlio — Vitrine de Imóveis em Uberlândia

Vitrine de imóveis em Uberlândia: imóveis de captação própria, lançamentos de
construtoras e o catálogo do portal parceiro Chave7, com o financiamento
(Caixa, Minha Casa Minha Vida, FGTS) resolvido pelo corretor.

A **autoridade do profissional** mora no site oficial
[marcotulio.pro](https://www.marcotulio.pro) — aqui a página só apresenta o
essencial e faz a ponte para lá. Este domínio é a vertente de **catálogo + SEO**.

🔗 **Ao vivo:** https://imoveis.marcotulio.pro

## Conteúdo
- `index.html` — página inteira (HTML/CSS/JS em arquivo único)
- `sitemap.xml` — mapa do site para buscadores
- `robots.txt` — diretrizes de indexação

## Como publicar um imóvel

Tudo fica em **um único lugar**: no `<script>` no fim do `index.html`, procure
por `PUBLICAR IMÓVEIS`. Existem dois arrays:

- `MEUS_IMOVEIS` → aba "Meus imóveis" (captação própria, selo azul)
- `LANCAMENTOS` → seção "Lançamentos" (superfície coral, selo coral)

Adicione um objeto no array correspondente:

```js
var MEUS_IMOVEIS = [
  {
    selo:    'Captação exclusiva',            // texto do selo
    titulo:  'Casa 3 quartos com quintal',
    local:   'Santa Mônica, Uberlândia',
    preco:   480000,                          // opcional, número sem pontuação
    img:     'https://.../foto.jpg',          // opcional
    quartos: 3,
    vagas:   2,
    area:    180,                             // em m²
    desc:    'Casa térrea reformada, a 5 minutos da UFU.'
  }
];
```

O que acontece automaticamente ao salvar:

1. O card aparece na página com preço formatado em reais e as características.
2. O link do card já abre o WhatsApp com uma mensagem citando aquele imóvel.
3. É gerado um **`ItemList` schema.org** com cada imóvel como `Accommodation` +
   `Offer` (preço, área, quartos, vendedor) — é isso que faz o Google entender o
   anúncio. **Este é o mecanismo de SEO dos imóveis.**

Enquanto os arrays ficam vazios, a página mostra um estado vazio honesto com CTA,
e **nenhum** schema é emitido (schema vazio é pior que schema nenhum).

### Ao publicar imóveis, atualize também
- `sitemap.xml`: o campo `<lastmod>`.
- Se o volume crescer muito, vale criar páginas individuais por imóvel — hoje o
  site é de página única.

## Integração dinâmica com o Chave7 (próximo passo)

Hoje o catálogo do Chave7 é um **link** para o portal, não uma importação: um
site estático não consegue puxar dados de outro domínio sem servidor
(o navegador bloqueia por CORS). Para puxar imóveis de verdade seria preciso um
destes caminhos:

1. **Netlify Function** (serverless) que consulta o Chave7 e devolve JSON — a
   página passa a fazer `fetch` nessa função.
2. **Build agendado**: um GitHub Action roda periodicamente, busca os imóveis e
   grava o array direto no HTML. Melhor para SEO, porque o conteúdo vai no HTML.
3. **Feed/exportação** que o Chave7 disponibilize (XML/CSV/API).

A opção 2 é a mais indicada para SEO. O array `MEUS_IMOVEIS` já é o ponto de
integração — é só passar a gerá-lo automaticamente.

## Stack
Site estático. Sem build, sem dependências. Única externa: Google Fonts
(Bricolage Grotesque + Hanken Grotesk).

## Deploy
Publicado no **Netlify**, a partir da branch `main` deste repositório.
