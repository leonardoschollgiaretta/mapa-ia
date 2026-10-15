# Cadeia de IA 2026

Site de página única com o mapa de relações entre as empresas da cadeia de
inteligência artificial (EUA, Taiwan, Coreia, Japão, China, Europa), ranking
por receita, projeção, valor de mercado e capex, e treemap de tamanho.

- Conteúdo: `static/mapa_cadeia_ia_2026.html` (HTML autossuficiente).
- App: `app.py` serve o HTML e registra acessos (`lib/acessos.py`).
- Contador: abra a URL com `?admin=1`.

## Rodar local

```
streamlit run app.py
```

## Publicar (Streamlit Cloud)

1. Novo app apontando para este repositório, branch `main`, arquivo `app.py`.
2. Em Settings → Secrets, colar `postgres_url = "..."` (URL do session pooler
   do Supabase, porta 6543). Sem isso o contador grava num SQLite que some a
   cada redeploy.

## Atualizar o conteúdo

Substituir `static/mapa_cadeia_ia_2026.html` pela versão nova e fazer push.
