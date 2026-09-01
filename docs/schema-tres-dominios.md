# O mesmo corretor nos três domínios

Para o Google, `marcotulio.pro`, `imoveis.marcotulio.pro` e
`simulador.marcotulio.pro` são três sites diferentes. O que faz ele entender
que por trás dos três está **a mesma pessoa** é um identificador de schema.org
repetido nos três, idêntico caractere por caractere:

```
https://marcotulio.pro/#marcotulio
```

## Como está hoje (conferido em 01/09/2026)

| domínio | identificador que ele usa | situação |
|---|---|---|
| `marcotulio.pro` | `https://marcotulio.pro/#marcotulio` | ✅ correto — é o dono do nó completo |
| `marcotulio.pro/sobre` | `https://marcotulio.pro/#marcotulio` | ✅ correto |
| `imoveis.marcotulio.pro` | `https://marcotulio.pro/#marcotulio` | ✅ corrigido |
| `simulador.marcotulio.pro` | `https://marcotulio.pro/**sobre**#marcotulio` | ❌ **aponta para o vazio** |

O simulador **tem** identificador — só que é outro. E não é "outro" no sentido
de apontar para uma segunda ficha: **ninguém declara `/sobre#marcotulio`**.
Nem a página `/sobre`, que usa `/#marcotulio` como todas as outras.

É um ponteiro para um endereço que não existe. Do ponto de vista do Google, o
simulador não está ligado a você.

---

## O conserto no `simulador.marcotulio.pro`

São **quatro trocas**, todas no JSON-LD do `<head>`. Nenhuma muda o que aparece
na tela.

### Bloco `Article` — trocar `author` e `publisher`

Está assim:

```json
"author": {
  "@type": "Person",
  "@id": "https://marcotulio.pro/sobre#marcotulio",
  "name": "Marco Túlio Andrade Freitas",
  "jobTitle": "Corretor de Imóveis",
  "url": "https://marcotulio.pro/sobre",
  "sameAs": ["https://marcotulio.pro/", "https://imoveis.marcotulio.pro/"]
},
"publisher": {
  "@type": "Person",
  "@id": "https://marcotulio.pro/sobre#marcotulio",
  "name": "Marco Túlio Andrade Freitas"
}
```

Troque pelas duas linhas:

```json
"author":    { "@id": "https://marcotulio.pro/#marcotulio" },
"publisher": { "@id": "https://marcotulio.pro/#marcotulio" }
```

### Bloco `WebApplication` — trocar `author` e `publisher`

Está assim (sem `@id` nenhum — dois nós anônimos):

```json
"author": {
  "@type": "Person",
  "name": "Marco Túlio Andrade Freitas",
  "url": "https://marcotulio.pro/sobre",
  "jobTitle": "Corretor de Imóveis"
},
"publisher": {
  "@type": "Person",
  "name": "Marco Túlio Andrade Freitas",
  "url": "https://marcotulio.pro"
}
```

Troque pelas mesmas duas linhas:

```json
"author":    { "@id": "https://marcotulio.pro/#marcotulio" },
"publisher": { "@id": "https://marcotulio.pro/#marcotulio" }
```

### Por que jogar fora nome, `jobTitle` e `sameAs`

Porque tudo isso já está no nó completo do `marcotulio.pro`, e lá está mais
completo: endereço, telefone, `knowsAbout` e **treze** `sameAs`, contra os dois
que o simulador lista.

**Referência não envelhece, cópia sim.** No dia em que você trocar o telefone
no `marcotulio.pro`, uma cópia passa a contradizê-lo — e duas fichas
divergentes com o mesmo nome são piores do que uma só. A referência não tem
como ficar desatualizada, porque não guarda dado nenhum.

Tem ainda um detalhe: o simulador declara `"@type": "Person"` e o
`marcotulio.pro` declara `"@type": "RealEstateAgent"`. Trocando pela referência
pura, esse conflito de tipo desaparece junto.

### Se preferir também um bloco próprio

Opcional. As quatro trocas acima já resolvem. Se quiser deixar explícito no
`<head>` do simulador:

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

---

## `marcotulio.pro` — não mexa

Está certo. O nó completo mora lá, com o `@id` e os treze `sameAs` (Maps,
Instagram, LinkedIn, Facebook, Threads, TikTok, YouTube, Pinterest, X, WhatsApp
e os dois subdomínios). É a base de tudo.

Só confira que `imoveis.marcotulio.pro` e `simulador.marcotulio.pro` continuam
na lista de `sameAs` — eles estão, e é isso que fecha o triângulo.

---

## `imoveis.marcotulio.pro` — já aplicado

Fica registrado, porque o mesmo raciocínio vale para o simulador.

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
   (`search.google.com/test/rich-results`), nos três domínios. O identificador
   tem que ser o mesmo nos três.
2. Nenhuma página pode declarar **dois** nós de pessoa com identificadores
   diferentes.
3. No Search Console, a consolidação leva semanas — é o Google reprocessando as
   três propriedades. Não é mudança de um dia para o outro.

Comando rápido para conferir os três de uma vez:

```sh
for u in https://marcotulio.pro/ https://imoveis.marcotulio.pro/ https://simulador.marcotulio.pro/; do
  echo "$u"
  curl -sSL "$u" | grep -o '"@id": *"[^"]*marcotulio[^"]*"' | sort -u
done
```

O esperado é `https://marcotulio.pro/#marcotulio` nos três, e mais nada.
