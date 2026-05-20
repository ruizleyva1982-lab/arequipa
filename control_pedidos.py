import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Entregas hacia MA AREQUIPA",
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
        bins=[-1, 0, 50, 99.9, 100],
        labels=["⛔ Sin entregar", "🟡 En proceso", "🔵 Casi completo", "✅ Completo"]
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
    st.markdown("### 📅 Filtros")
    # Filtro de estado (se llenará tras cargar datos)
    estados_opciones = ["Todos", "⛔ Sin entregar", "🟡 En proceso", "🔵 Casi completo", "✅ Completo"]
    filtro_estado = st.selectbox("Estado de entrega", estados_opciones)

    buscar = st.text_input("🔍 Buscar producto", placeholder="Código o descripción")

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
    <h1>📦 Control de Entregas MA AREQUIPA</h1>
    <p>Seguimiento de productos entregadosl</p>
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
# GRÁFICO GLOBAL – AVANCE TOTAL
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Avance Global por Producto</div>', unsafe_allow_html=True)

df_plot = df_resumen.sort_values("PCT", ascending=True)
colors_bar = df_plot["PCT"].apply(
    lambda x: "#27ae60" if x >= 100 else ("#3498db" if x >= 50 else ("#e67e22" if x > 0 else "#e74c3c"))
)

fig_global = go.Figure()
fig_global.add_trace(go.Bar(
    x=df_plot["PCT"],
    y=df_plot["DESCRIPCIÓN"].str[:45],
    orientation="h",
    marker_color=colors_bar,
    text=df_plot["PCT"].apply(lambda x: f"{x}%"),
    textposition="outside",
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Avance: %{x}%<br>"
        "<extra></extra>"
    ),
))
fig_global.add_vline(x=100, line_dash="dot", line_color="#1e3a5f", line_width=1.5,
                     annotation_text="100%", annotation_font_color="#1e3a5f")
fig_global.update_layout(
    xaxis=dict(range=[0, 115], title="% Entregado", ticksuffix="%"),
    yaxis=dict(title=""),
    height=max(400, len(df_plot) * 26),
    margin=dict(l=10, r=60, t=20, b=30),
    paper_bgcolor="white",
    plot_bgcolor="#f8f9fa",
    showlegend=False,
)
st.plotly_chart(fig_global, use_container_width=True)

# ─────────────────────────────────────────────
# TABLA DETALLE POR PRODUCTO
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Detalle por Producto</div>', unsafe_allow_html=True)

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
# SECCIÓN: ENTREGAS POR DÍA
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">📅 Entregas por Día</div>', unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns([2, 1])
with col_sel1:
    producto_sel = st.selectbox(
        "Selecciona un producto para ver su detalle diario",
        options=df_resumen.sort_values("DESCRIPCIÓN")["CÓDIGO"].tolist(),
        format_func=lambda c: f"{c} – {df_resumen.loc[df_resumen['CÓDIGO']==c,'DESCRIPCIÓN'].values[0][:60]}",
    )
with col_sel2:
    vista = st.radio("Vista", ["Barras", "Acumulado"], horizontal=True)

prod_info = df_resumen[df_resumen["CÓDIGO"] == producto_sel].iloc[0]
ent_prod  = df_ent[df_ent["Número de artículo"] == producto_sel].copy()

if ent_prod.empty:
    st.info(f"⚠️ No hay entregas registradas aún para **{prod_info['DESCRIPCIÓN']}**.")
else:
    ent_dia = (
        ent_prod.groupby("Fecha de vencimiento")["Cantidad"]
        .sum()
        .reset_index()
        .sort_values("Fecha de vencimiento")
    )
    ent_dia["Fecha_str"]   = ent_dia["Fecha de vencimiento"].dt.strftime("%d/%m/%Y")
    ent_dia["Acumulado"]   = ent_dia["Cantidad"].cumsum()
    ent_dia["Pct_Acum"]    = (ent_dia["Acumulado"] / prod_info["REQUERIMIENTO"] * 100).clip(upper=100)

    if vista == "Barras":
        fig_dia = go.Figure()
        fig_dia.add_trace(go.Bar(
            x=ent_dia["Fecha_str"],
            y=ent_dia["Cantidad"],
            marker_color="#3498db",
            text=ent_dia["Cantidad"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
            name="Entregado por día",
        ))
        fig_dia.update_layout(
            xaxis_title="Fecha de entrega",
            yaxis_title="Cantidad",
            title=f"Entregas diarias: {prod_info['DESCRIPCIÓN'][:50]}",
            height=380,
            margin=dict(t=50, b=40),
            plot_bgcolor="#f8f9fa",
        )
    else:
        fig_dia = go.Figure()
        fig_dia.add_trace(go.Scatter(
            x=ent_dia["Fecha_str"],
            y=ent_dia["Acumulado"],
            mode="lines+markers+text",
            line=dict(color="#2d6a4f", width=3),
            marker=dict(size=9, color="#2d6a4f"),
            text=ent_dia["Acumulado"].apply(lambda x: f"{x:,.0f}"),
            textposition="top center",
            name="Acumulado",
        ))
        fig_dia.add_hline(
            y=prod_info["REQUERIMIENTO"],
            line_dash="dot", line_color="#e74c3c", line_width=2,
            annotation_text=f"Req: {int(prod_info['REQUERIMIENTO']):,}",
            annotation_font_color="#e74c3c",
        )
        fig_dia.update_layout(
            xaxis_title="Fecha de entrega",
            yaxis_title="Cantidad acumulada",
            title=f"Avance acumulado: {prod_info['DESCRIPCIÓN'][:50]}",
            height=380,
            margin=dict(t=50, b=40),
            plot_bgcolor="#f8f9fa",
        )

    st.plotly_chart(fig_dia, use_container_width=True)

    # Mini tabla de entregas del producto
    st.markdown("**📄 Detalle de entregas registradas:**")
    tbl_ent = ent_dia[["Fecha_str", "Cantidad", "Acumulado", "Pct_Acum"]].copy()
    tbl_ent.columns = ["Fecha", "Cantidad del día", "Acumulado", "% Avance"]
    st.dataframe(
        tbl_ent.style.format({
            "Cantidad del día": "{:,.0f}",
            "Acumulado": "{:,.0f}",
            "% Avance": "{:.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Resumen rápido del producto seleccionado
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Requerido",  f"{int(prod_info['REQUERIMIENTO']):,}")
    col_b.metric("Entregado",  f"{int(prod_info['ENTREGADO']):,}")
    col_c.metric("Faltante",   f"{int(prod_info['FALTANTE']):,}",
                 delta=f"-{int(prod_info['FALTANTE']):,}" if prod_info["FALTANTE"] > 0 else "Completo",
                 delta_color="inverse")
    col_d.metric("Avance",     f"{prod_info['PCT']:.1f}%")

# ─────────────────────────────────────────────
# GRÁFICO DONA – ESTADO GENERAL
# ─────────────────────────────────────────────
st.markdown('<div class="section-title">🍩 Distribución por Estado</div>', unsafe_allow_html=True)

estado_counts = df_resumen["ESTADO"].value_counts()
fig_dona = go.Figure(go.Pie(
    labels=estado_counts.index.tolist(),
    values=estado_counts.values.tolist(),
    hole=0.55,
    marker_colors=["#27ae60", "#3498db", "#e67e22", "#e74c3c"],
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>Productos: %{value}<br>%{percent}<extra></extra>",
))
fig_dona.add_annotation(
    text=f"<b>{pct_global}%</b><br>global",
    x=0.5, y=0.5, showarrow=False,
    font=dict(size=18, color="#1e3a5f"),
)
fig_dona.update_layout(height=340, margin=dict(t=20, b=20), showlegend=True)

col_dona, col_heat = st.columns([1, 2])
with col_dona:
    st.plotly_chart(fig_dona, use_container_width=True)

# Heatmap de entregas por producto por día
with col_heat:
    st.markdown("**📆 Mapa de calor – Entregas por día**")
    pivot = (
        df_ent.groupby(["Número de artículo", "Fecha de vencimiento"])["Cantidad"]
        .sum()
        .reset_index()
    )
    pivot["Fecha_str"] = pivot["Fecha de vencimiento"].dt.strftime("%d/%m")
    # Filtrar solo los del pedido
    pivot = pivot[pivot["Número de artículo"].isin(df_ped["CÓDIGO"])]
    pivot_table = pivot.pivot_table(
        index="Número de artículo", columns="Fecha_str", values="Cantidad", aggfunc="sum", fill_value=0
    )

    if not pivot_table.empty:
        fig_heat = px.imshow(
            pivot_table,
            aspect="auto",
            color_continuous_scale="YlGn",
            labels={"color": "Cantidad"},
        )
        fig_heat.update_layout(
            height=340,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="Fecha",
            yaxis_title="Código",
            coloraxis_showscale=True,
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Sin datos para mostrar en el mapa de calor.")

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
