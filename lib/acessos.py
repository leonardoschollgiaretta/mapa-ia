"""
acessos.py — contador de acessos das páginas do site.

Grava uma linha por visita (uma por sessão do Streamlit) e devolve totais.

Onde grava:
  • Streamlit Cloud: Postgres (Supabase), se existir st.secrets["postgres_url"]
    ou a variável de ambiente POSTGRES_URL. O disco da nuvem é efêmero, então
    só um banco externo preserva a contagem entre redeploys.
  • Local / sem secret: SQLite em data/acessos.db (pasta ignorada no git).

Nunca grava IP puro: guarda só um hash curto, suficiente para contar
visitantes distintos por dia sem identificar ninguém.
"""
import hashlib
import os
import sqlite3
from datetime import datetime, timezone

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raiz do app
_SQLITE = os.path.join(_BASE, "data", "acessos.db")

_DDL = """
CREATE TABLE IF NOT EXISTS acessos (
    id        {serial},
    ts        TEXT NOT NULL,
    pagina    TEXT NOT NULL,
    visitante TEXT,
    agente    TEXT
)
"""


def _url_postgres():
    u = os.environ.get("POSTGRES_URL")
    if u:
        return u.strip()
    try:
        import streamlit as st
        if "postgres_url" in st.secrets:
            return str(st.secrets["postgres_url"]).strip()
    except Exception:
        pass
    return None


def _conectar():
    """Devolve (conexao, tipo) com tipo 'pg' ou 'sqlite'."""
    url = _url_postgres()
    if url:
        import psycopg
        con = psycopg.connect(url, autocommit=True, connect_timeout=8)
        with con.cursor() as cur:
            cur.execute(_DDL.format(serial="SERIAL PRIMARY KEY"))
        return con, "pg"
    os.makedirs(os.path.dirname(_SQLITE), exist_ok=True)
    con = sqlite3.connect(_SQLITE)
    con.execute(_DDL.format(serial="INTEGER PRIMARY KEY AUTOINCREMENT"))
    con.commit()
    return con, "sqlite"


def _contexto():
    """Hash curto do IP e user-agent, quando o Streamlit expõe os headers."""
    ip = ua = ""
    try:
        import streamlit as st
        h = st.context.headers
        ip = h.get("X-Forwarded-For", "") or h.get("X-Real-Ip", "") or ""
        ua = h.get("User-Agent", "") or ""
    except Exception:
        pass
    ip = ip.split(",")[0].strip()
    vis = hashlib.sha256(f"{ip}|{ua}".encode()).hexdigest()[:16] if (ip or ua) else None
    return vis, ua[:200] if ua else None


def registrar(pagina):
    """Grava uma visita. Silencioso em caso de erro (nunca derruba a página)."""
    try:
        import streamlit as st
        chave = f"_acesso_{pagina}"
        if st.session_state.get(chave):
            return False
        st.session_state[chave] = True
    except Exception:
        pass
    try:
        con, tipo = _conectar()
        vis, ua = _contexto()
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        q = "INSERT INTO acessos (ts, pagina, visitante, agente) VALUES (%s, %s, %s, %s)" \
            if tipo == "pg" else \
            "INSERT INTO acessos (ts, pagina, visitante, agente) VALUES (?, ?, ?, ?)"
        if tipo == "pg":
            with con.cursor() as cur:
                cur.execute(q, (ts, pagina, vis, ua))
        else:
            con.execute(q, (ts, pagina, vis, ua))
            con.commit()
        con.close()
        return True
    except Exception:
        return False


def resumo(pagina):
    """Totais da página: dict com total, visitantes distintos, últimos 7 dias
    e série por dia (lista de (dia, visitas, visitantes)). None se falhar."""
    try:
        con, tipo = _conectar()
        p = "%s" if tipo == "pg" else "?"
        q = f"SELECT substr(ts,1,10) AS dia, COUNT(*), COUNT(DISTINCT visitante) " \
            f"FROM acessos WHERE pagina = {p} GROUP BY dia ORDER BY dia"
        if tipo == "pg":
            with con.cursor() as cur:
                cur.execute(q, (pagina,))
                linhas = cur.fetchall()
        else:
            linhas = con.execute(q, (pagina,)).fetchall()
        con.close()
        total = sum(r[1] for r in linhas)
        hoje = datetime.now(timezone.utc).date()
        ult7 = sum(r[1] for r in linhas
                   if (hoje - datetime.strptime(r[0], "%Y-%m-%d").date()).days < 7)
        return {"total": total, "ult7": ult7, "dias": linhas, "onde": tipo}
    except Exception:
        return None
