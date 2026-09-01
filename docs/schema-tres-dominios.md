# O mesmo corretor nos três domínios

Para o Google, `marcotulio.pro`, `imoveis.marcotulio.pro` e
`simulador.marcotulio.pro` são três sites diferentes. O que faz ele entender
que por trás dos três está **a mesma pessoa** é um identificador de schema.org
repetido nos três, idêntico caractere por caractere:

```
https://marcotulio.pro/#marcotulio
```

Esse `@id` **já existe** no `marcotulio.pro`. Não invente outro, não troque a
barra final, não use `www`, não use `imoveis.` no lugar. Um caractere diferente
e o Google volta a ver duas pessoas.

## Como está dividido

| domínio | o que carrega |
|---|---|
| `marcotulio.pro` | o **nó completo**: nome, endereço, telefone, `knowsAbout` e os 13 `sameAs`. É o domínio de autoridade. |
| `imoveis.marcotulio.pro` | uma **referência** ao `@id` — já aplicado |
| `simulador.marcotulio.pro` | uma **referência** ao `@id` — falta aplicar |

**Referência, e não cópia.** Cópia envelhece: no dia em que você trocar o
telefone no `marcotulio.pro`, os outros dois passam a contradizê-lo, e duas
fichas divergentes com o mesmo nome são piores do que uma só. A referência não
tem como ficar desatualizada, porque não guarda dado nenhum.

---

## 1. `marcotulio.pro` — não mexa

Já está certo. O nó completo está lá, com o `@id` e os 13 `sameAs` (Google
Maps, Instagram, LinkedIn, Facebook, Threads, TikTok, YouTube, Pinterest, X,
WhatsApp e os dois subdomínios). É a base de tudo.

Só confira que `imoveis.marcotulio.pro` e `simulador.marcotulio.pro` continuam
na lista de `sameAs` — eles estão, e é isso que fecha o triângulo.

---

## 2. `simulador.marcotulio.pro` — colar isto

Hoje o simulador tem quatro blocos (`WebApplication`, `FAQPage`, `Article`,
`BreadcrumbList`) e **nenhum** liga a página a você. Cole este bloco no
`<head>`, junto dos outros:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "RealEstateAgent",
  "@id": "https://marcotulio.pro/#marcotulio",
  "name": "Marco Túlio Andrade Freitas",
  "url": "https://marcotulio.pro"
}
</script>
```

E, no bloco `WebApplication` que já existe lá, acrescente estas duas linhas
para dizer quem oferece a ferramenta:

```json
  "provider": { "@id": "https://marcotulio.pro/#marcotulio" },
  "author":   { "@id": "https://marcotulio.pro/#marcotulio" }
```

Se o `FAQPage` do simulador também for seu conteúdo, vale acrescentar nele:

```json
  "author": { "@id": "https://marcotulio.pro/#marcotulio" }
```

---

## 3. `imoveis.marcotulio.pro` — já aplicado

Fica registrado o que foi feito aqui, porque o mesmo raciocínio vale para o
simulador.

**O problema era maior do que o bloco do `<head>`.** A página declarava um
`RealEstateAgent` completo **sem `@id`** — uma segunda ficha, competindo com a
do `marcotulio.pro` — e, além dele, **23 `RealEstateAgent` anônimos**, um como
`seller` de cada oferta de imóvel. Para o Google eram **24 pessoas diferentes**,
todas chamadas Marco Túlio.

Agora são 25 referências ao mesmo `@id`, e nó de pessoa nenhum sem
identificador:

- o nó de referência no `<head>`
- `publisher` do `WebSite`
- `seller` das 23 ofertas do `ItemList`
- `seller` da oferta em cada página de imóvel

No código, o identificador mora em **um lugar só**: a constante `ENTIDADE`, no
topo de `tools/gerar.py`.

---

## Como conferir depois de publicar

1. **Teste de Resultados Aprimorados** do Google
   (`search.google.com/test/rich-results`) em cada um dos três domínios. O
   `RealEstateAgent` tem que aparecer nos três com o mesmo `@id`.
2. Nenhum dos três pode mostrar **dois** `RealEstateAgent` na mesma página.
3. No Search Console, a consolidação leva semanas para aparecer — é o Google
   reprocessando as três propriedades. Não é mudança de um dia para o outro.
