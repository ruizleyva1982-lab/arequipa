import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Control de Pedidos",
    page_icon="📦",
    layout="wide",
)

# ─────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a4f 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p  { margin: 0.2rem 0 0; font-size: 0.9rem; opacity: 0.85; }

    .update-banner {
        background: #f0f9f4;
        border-left: 4px solid #2d6a4f;
        padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.85rem;
        color: #2d6a4f;
        margin-bottom: 1.2rem;
    }

    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 4px solid;
    }
    .kpi-card .kpi-val  { font-size: 2rem; font-weight: 700; }
    .kpi-card .kpi-lbl  { font-size: 0.78rem; color: #666; margin-top: 2px; }

    .product-table th {
        background: #1e3a5f !important;
        color: white !important;
    }

    .stButton > button {
        background: #2d6a4f;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton > button:hover { background: #1e3a5f; }

    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e3a5f;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.3rem;
        margin: 1.5rem 0 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cargar_datos(filepath: str, mtime: float):
    """Lee el Excel y retorna los dos dataframes + metadatos."""
    df_ped = pd.read_excel(filepath, sheet_name="Pedido")
    df_ent = pd.read_excel(filepath, sheet_name="Entregas")

    df_ped.columns = df_ped.columns.str.strip()
    df_ent.columns = df_ent.columns.str.strip()

    df_ped["FECHA PEDIDO"] = pd.to_datetime(df_ped["FECHA PEDIDO"])
    df_ent["Fecha de vencimiento"] = pd.to_datetime(df_ent["Fecha de vencimiento"])

    # Solo entregas de productos que están en el pedido
    codigos_pedido = df_ped["CÓDIGO"].unique()
    df_ent_filtrado = df_ent[df_ent["Número de artículo"].isin(codigos_pedido)].copy()

    return df_ped, df_ent_filtrado


def construir_resumen(df_ped, df_ent):
    """DataFrame consolidado por producto con totales y porcentaje."""
    entregado = (
        df_ent.groupby("Número de artículo")["Cantidad"]
        .sum()
        .reset_index()
        .rename(columns={"Número de artículo": "CÓDIGO", "Cantidad": "ENTREGADO"})
    )
    df = df_ped.merge(entregado, on="CÓDIGO", how="left")
    df["ENTREGADO"] = df["ENTREGADO"].fillna(0)
    df["FALTANTE"] = (df["REQUERIMIENTO"] - df["ENTREGADO"]).clip(lower=0)
    df["PCT"] = ((df["ENTREGADO"] / df["REQUERIMIENTO"]) * 100).clip(upper=100).round(1)
    df["ESTADO"] = pd.cut(
        df["PCT"],
        bins=[-1, 0, 99.9, 100],
        labels=["⛔ Sin entregar", "🟡 En proceso", "✅ Completo"]
    )
    return df


def color_pct(val):
    if val == 0:
        return "color: #e74c3c; font-weight:700"
    elif val < 50:
        return "color: #e67e22; font-weight:700"
    elif val < 100:
        return "color: #3498db; font-weight:700"
    else:
        return "color: #27ae60; font-weight:700"


def color_faltante(val):
    if val > 0:
        return "color: #e74c3c"
    return "color: #27ae60"


# ─────────────────────────────────────────────
# SIDEBAR – subir archivo
# ─────────────────────────────────────────────
with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    
    st.markdown("## ⚙️ Configuración")

    DEFAULT_PATH = "bd.xlsx"

    uploaded = st.file_uploader(
        "📂 Actualizar Excel",
        type=["xlsx"],
        help="Sube tu bd.xlsx actualizado para refrescar la app.",
    )

    if uploaded:
        with open(DEFAULT_PATH, "wb") as f:
            f.write(uploaded.read())
        st.cache_data.clear()
        st.success("✅ Archivo actualizado")

    # Determinar qué archivo usar
    if os.path.exists(DEFAULT_PATH):
        FILEPATH = DEFAULT_PATH
    else:
        st.warning("Sube tu archivo bd.xlsx para comenzar.")
        st.stop()

    mtime = os.path.getmtime(FILEPATH)
    dt_mod = datetime.fromtimestamp(mtime)

    st.markdown("---")
    st.caption("© Maria Almenara – Control de Pedidos")

# ─────────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────────
df_ped, df_ent = cargar_datos(FILEPATH, mtime)
df_resumen = construir_resumen(df_ped, df_ent)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>📦 Control de Pedidos</h1>
    <p>Maria Almenara · Seguimiento de entregas en tiempo real</p>
</div>
""", unsafe_allow_html=True)

# Banner de actualización
st.markdown(f"""
<div class="update-banner">
    🕐 <b>Última actualización del archivo:</b>&nbsp; {dt_mod.strftime("%d/%m/%Y %H:%M:%S")}
    &nbsp;·&nbsp; Archivo: <code>{os.path.basename(FILEPATH)}</code>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KPIs GLOBALES
# ─────────────────────────────────────────────
total_prod   = len(df_resumen)
total_req    = int(df_resumen["REQUERIMIENTO"].sum())
total_ent    = int(df_resumen["ENTREGADO"].sum())
total_falt   = int(df_resumen["FALTANTE"].sum())
pct_global   = round(total_ent / total_req * 100, 1) if total_req > 0 else 0
completos    = int((df_resumen["PCT"] >= 100).sum())

c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (c1, "#1e3a5f", f"{total_prod}", "Productos en pedido"),
    (c2, "#2d6a4f", f"{total_req:,}", "Unidades requeridas"),
    (c3, "#3498db", f"{total_ent:,}", "Unidades entregadas"),
    (c4, "#e74c3c", f"{total_falt:,}", "Unidades faltantes"),
    (c5, "#27ae60", f"{pct_global}%", "Avance global"),
]
for col, color, val, lbl in kpis:
    col.markdown(f"""
    <div class="kpi-card" style="border-top-color:{color}">
        <div class="kpi-val" style="color:{color}">{val}</div>
        <div class="kpi-lbl">{lbl}</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABLA DETALLE POR PRODUCTO
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Detalle por Producto</div>', unsafe_allow_html=True)

# Filtros justo encima de la tabla
estados_opciones = ["Todos", "⛔ Sin entregar", "🟡 En proceso", "✅ Completo"]
fcol1, fcol2 = st.columns([1, 2])
with fcol1:
    filtro_estado = st.selectbox("🏷️ Estado de entrega", estados_opciones, key="filtro_estado")
with fcol2:
    buscar = st.text_input("🔍 Buscar por código o descripción", placeholder="Ej: M1020110 o BROWNIE", key="buscar")

# Aplicar filtros
df_tabla = df_resumen.copy()
if filtro_estado != "Todos":
    df_tabla = df_tabla[df_tabla["ESTADO"].astype(str) == filtro_estado]
if buscar:
    mask = (
        df_tabla["CÓDIGO"].str.contains(buscar, case=False, na=False) |
        df_tabla["DESCRIPCIÓN"].str.contains(buscar, case=False, na=False)
    )
    df_tabla = df_tabla[mask]

cols_show = ["CÓDIGO", "DESCRIPCIÓN", "UMI", "REQUERIMIENTO", "ENTREGADO", "FALTANTE", "PCT", "ESTADO", "FECHA PEDIDO"]
df_display = df_tabla[cols_show].copy()
df_display["FECHA PEDIDO"] = df_display["FECHA PEDIDO"].dt.strftime("%d/%m/%Y")
df_display["REQUERIMIENTO"] = df_display["REQUERIMIENTO"].apply(lambda x: f"{x:,}")
df_display["ENTREGADO"]     = df_display["ENTREGADO"].apply(lambda x: f"{int(x):,}")
df_display["FALTANTE"]      = df_display["FALTANTE"].apply(lambda x: f"{int(x):,}")

st.dataframe(
    df_tabla[cols_show].style
        .map(color_pct, subset=["PCT"])
        .map(color_faltante, subset=["FALTANTE"])
        .format({
            "REQUERIMIENTO": "{:,.0f}",
            "ENTREGADO": "{:,.0f}",
            "FALTANTE": "{:,.0f}",
            "PCT": "{:.1f}%",
            "FECHA PEDIDO": lambda x: x.strftime("%d/%m/%Y") if hasattr(x, "strftime") else x,
        }),
    use_container_width=True,
    height=420,
)

st.caption(f"Mostrando {len(df_tabla)} de {len(df_resumen)} productos")

# ─────────────────────────────────────────────
# SECCIÓN: ENTREGAS POR DÍA – TABLA TIPO MATRIZ
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📅 Entregas por Día – Tabla por Producto</div>', unsafe_allow_html=True)

# Construir pivot: productos del pedido × fechas de entrega
ent_pedido = df_ent[df_ent["Número de artículo"].isin(df_ped["CÓDIGO"])].copy()

if ent_pedido.empty:
    st.info("⚠️ No hay entregas registradas aún.")
else:
    ent_pedido["Dia"] = ent_pedido["Fecha de vencimiento"].dt.day.astype(str)
    
    ent_pedido["Fecha_col"] = ent_pedido["Fecha de vencimiento"].dt.strftime("%d/%m/%Y")

    pivot = (
        ent_pedido.groupby(["Número de artículo", "Fecha_col"])["Cantidad"]
        .sum()
        .reset_index()
    )
    # Orden cronológico de fechas
    fechas_ordenadas = (
        ent_pedido[["Fecha de vencimiento", "Fecha_col"]]
        .drop_duplicates()
        .sort_values("Fecha de vencimiento")["Fecha_col"]
        .tolist()
    )
    pivot_table = pivot.pivot_table(
        index="Número de artículo",
        columns="Fecha_col",
        values="Cantidad",
        aggfunc="sum",
        fill_value=0,
    )
    # Reordenar columnas cronológicamente
    cols_ord = [f for f in fechas_ordenadas if f in pivot_table.columns]
    pivot_table = pivot_table[cols_ord]

    # Agregar descripción como índice
    desc_map = df_ped.set_index("CÓDIGO")["DESCRIPCIÓN"].to_dict()
    pivot_table.index = [desc_map.get(c, c) for c in pivot_table.index]
    pivot_table = pivot_table.sort_index()
    pivot_table.columns.name = "Fecha"

    # Construir tabla HTML directamente
    fechas = pivot_table.columns.tolist()
    html = """
    <style>
    .tabla-entregas { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
    .tabla-entregas th {
        background-color: #c0392b; color: white; font-weight: bold;
        padding: 8px 12px; text-align: center; border: 1px solid #ddd;
    }
    .tabla-entregas th.col-prod {
        text-align: left; min-width: 220px;
    }
    .tabla-entregas td.col-prod {
        padding: 7px 10px; border: 1px solid #eee;
        background: white; color: #333; font-size: 0.82rem;
    }
    .tabla-entregas td.celda-cero {
        background: white; color: #ccc; text-align: center;
        padding: 7px 10px; border: 1px solid #eee;
    }
    .tabla-entregas td.celda-valor {
        background: #d4edda; color: #1a6b35; text-align: center;
        font-weight: 600; padding: 7px 10px; border: 1px solid #eee;
    }
    .tabla-entregas tr:nth-child(even) td.col-prod { background: #f9f9f9; }
    </style>
    <div style="overflow-x:auto; max-height:600px; overflow-y:auto;">
    <table class="tabla-entregas">
    <thead><tr>
    <th class="col-prod">PRODUCTO</th>
    """
    for f in fechas:
        html += f"<th>{f}</th>"
    html += "</tr></thead><tbody>"

    for prod, row in pivot_table.iterrows():
        html += f"<tr><td class='col-prod'>{prod}</td>"
        for f in fechas:
            val = int(row[f])
            if val == 0:
                html += f"<td class='celda-cero'>0</td>"
            else:
                html += f"<td class='celda-valor'>{val:,}</td>"
        html += "</tr>"

    html += "</tbody></table></div>"

    st.markdown(html, unsafe_allow_html=True)
    st.caption(f"Mostrando {len(pivot_table)} productos · Fechas con entregas registradas")

# ─────────────────────────────────────────────
# GRÁFICO DONA – ESTADO GENERAL
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">🍩 Distribución por Estado</div>', unsafe_allow_html=True)

estado_counts = df_resumen["ESTADO"].value_counts()
fig_dona = go.Figure(go.Pie(
    labels=estado_counts.index.tolist(),
    values=estado_counts.values.tolist(),
    hole=0.55,
    marker_colors=["#27ae60", "#e67e22", "#e74c3c"],
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>Productos: %{value}<br>%{percent}<extra></extra>",
))
fig_dona.add_annotation(
    text=f"<b>{pct_global}%</b><br>global",
    x=0.5, y=0.5, showarrow=False,
    font=dict(size=18, color="#1e3a5f"),
)
fig_dona.update_layout(height=340, margin=dict(t=20, b=20), showlegend=True)
col_dona, _ = st.columns([1, 1])
with col_dona:
    st.plotly_chart(fig_dona, use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#aaa;font-size:0.8rem'>"
    "Control de Pedidos · Maria Almenara · Generado con Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
