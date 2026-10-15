"""
app.py — site "Cadeia de IA 2026": mapa de relações, ranking e treemap.

Site de página única. Todo o conteúdo é o HTML autossuficiente em
static/mapa_cadeia_ia_2026.html (gerado no levantamento de 14-15/10/2026);
o Streamlit só serve o arquivo e registra o acesso em lib/acessos.py.

Rodar local:  streamlit run app.py
Contador:     acrescente ?admin=1 à URL para ver os acessos por dia.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import streamlit.components.v1 as components

from lib import acessos

PAGINA = "mapa_ia"
_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "static", "mapa_cadeia_ia_2026.html")

st.set_page_config(page_title="Cadeia de IA 2026", page_icon="🧭", layout="wide",
                   initial_sidebar_state="collapsed")

# página única: esconde o menu lateral e aperta as margens para o mapa
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
.block-container { padding-top: 3.2rem; padding-bottom: 0; max-width: 1680px; }
header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

acessos.registrar(PAGINA)

try:
    with open(_HTML, encoding="utf-8") as f:
        html = f.read()
except OSError:
    st.error("Arquivo do mapa não encontrado (static/mapa_cadeia_ia_2026.html).")
    st.stop()

components.html(
    '<!doctype html><html><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<style>html,body{margin:0;background:#f4f5f7}</style></head><body>'
    + html + '</body></html>',
    height=2700, scrolling=True,
)

# ---------- contador (só com ?admin=1) ----------
if st.query_params.get("admin") == "1":
    r = acessos.resumo(PAGINA)
    with st.expander("Acessos", expanded=True):
        if not r:
            st.warning("Contador indisponível: sem banco configurado "
                       "(postgres_url nos secrets) ou erro de conexão.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Visitas (total)", r["total"])
            c2.metric("Visitas (7 dias)", r["ult7"])
            c3.metric("Banco", "Supabase" if r["onde"] == "pg" else "SQLite local")
            if r["dias"]:
                import pandas as pd
                df = pd.DataFrame(r["dias"], columns=["dia", "visitas", "visitantes"])
                st.bar_chart(df.set_index("dia")[["visitas", "visitantes"]])
                st.dataframe(df.sort_values("dia", ascending=False),
                             hide_index=True, width="stretch")
