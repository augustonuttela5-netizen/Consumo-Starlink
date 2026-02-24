import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Dashboard de Consumo")
st.title("📊 Dashboard de Consumo - Bases e Tráfego")

# -------------------------------------------------
# CONVERSÃO (MB, GB, TB → GB)
# -------------------------------------------------
def converter_para_gb(valor):
    if pd.isna(valor):
        return 0

    valor = str(valor).strip().upper().replace(" ", "").replace(",", ".")

    if "TB" in valor:
        return float(valor.replace("TB", "")) * 1024
    elif "GB" in valor:
        return float(valor.replace("GB", ""))
    elif "MB" in valor:
        return float(valor.replace("MB", "")) / 1024
    else:
        return float(valor)

# -------------------------------------------------
# FORMATAR COM UNIDADE
# -------------------------------------------------
def formatar_unidade(valor):
    if valor >= 1024:
        return f"{valor/1024:.2f} TB"
    else:
        return f"{valor:.2f} GB"

# -------------------------------------------------
# CARREGAR DADOS
# -------------------------------------------------
@st.cache_data
def carregar_dados():
    df_bases = pd.read_csv("starlink_bases.csv")
    df_trafego = pd.read_csv("trafego_carros.csv")

    df_bases.columns = df_bases.columns.str.strip()
    df_trafego.columns = df_trafego.columns.str.strip()

    for df in [df_bases, df_trafego]:
        df["CONSUMO_INICIAL_GB"] = df["CONSUMO_INICIAL"].apply(converter_para_gb)
        df["CONSUMO_FINAL_GB"] = df["CONSUMO_FINAL"].apply(converter_para_gb)
        df["DIFERENCA_GB"] = df["CONSUMO_FINAL_GB"] - df["CONSUMO_INICIAL_GB"]

    return df_bases, df_trafego

df_bases, df_trafego = carregar_dados()

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
tipo = st.sidebar.selectbox(
    "Selecionar tipo de dado",
    ["Bases Starlink", "Tráfego de Carros"]
)

if tipo == "Bases Starlink":
    df = df_bases.copy()
    label_col = "LOCALIDADE"
else:
    df = df_trafego.copy()
    label_col = "PLACA"

df = df.sort_values("CONSUMO_FINAL_GB")

data_inicial = df["DATA_INICIAL"].iloc[0]
data_final = df["DATA_FINAL"].iloc[0]

# -------------------------------------------------
# KPIs
# -------------------------------------------------
st.subheader("📌 Indicadores Gerais")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Consumo Total", formatar_unidade(df["DIFERENCA_GB"].sum()))
col2.metric("Maior Consumo", formatar_unidade(df["DIFERENCA_GB"].max()))
col3.metric("Média Consumo", formatar_unidade(df["DIFERENCA_GB"].mean()))
col4.metric("Total Monitorados", df.shape[0])

st.divider()

# -------------------------------------------------
# TABELA
# -------------------------------------------------
st.subheader(f"📋 Consumo detalhado - {tipo}")

st.dataframe(
    df[[
        "NOMES",
        "DATA_INICIAL",
        "CONSUMO_INICIAL",
        "DATA_FINAL",
        "CONSUMO_FINAL",
        label_col,
        "DIFERENCA_GB"
    ]],
    use_container_width=True
)

st.divider()

# -------------------------------------------------
# GRÁFICO VERTICAL PADRÃO
# -------------------------------------------------
st.subheader(f"📊 Comparativo de Consumo - {tipo}")

fig = go.Figure()

fig.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["CONSUMO_INICIAL_GB"],
    name=data_inicial,
    text=df["CONSUMO_INICIAL_GB"].apply(formatar_unidade),
    textposition="outside"
))

fig.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["CONSUMO_FINAL_GB"],
    name=data_final,
    text=df["CONSUMO_FINAL_GB"].apply(formatar_unidade),
    textposition="outside"
))

fig.update_layout(
    template="plotly_dark",
    barmode="group",
    height=650,
    xaxis_tickangle=-45,
    font=dict(size=16),
    yaxis_title="Consumo (GB / TB)",
    margin=dict(t=80)
)

fig.update_traces(
    cliponaxis=False
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------------------------------------
# GRÁFICO CONSUMO REAL
# -------------------------------------------------
st.subheader(f"📈 Consumo Real no Período - {tipo}")

fig_diff = go.Figure()

fig_diff.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["DIFERENCA_GB"],
    text=df["DIFERENCA_GB"].apply(formatar_unidade),
    textposition="outside"
))

fig_diff.update_layout(
    template="plotly_dark",
    height=600,
    xaxis_tickangle=-45,
    font=dict(size=16),
    yaxis_title="Consumo no Período (GB / TB)",
    margin=dict(t=80)
)

fig_diff.update_traces(
    cliponaxis=False
)

st.plotly_chart(fig_diff, use_container_width=True)

st.divider()

# -------------------------------------------------
# RANKING
# -------------------------------------------------
st.markdown("## 🚨 Maiores consumos da semana")

top5 = df.sort_values("DIFERENCA_GB", ascending=False).head(5).reset_index(drop=True)
top5["Ranking"] = top5.index + 1

def icone_alerta(posicao):
    if posicao == 1:
        return "🔴"
    elif posicao in [2, 3]:
        return "🟡"
    else:
        return "🔹"

top5["Alerta"] = top5["Ranking"].apply(icone_alerta)

st.dataframe(
    top5[["Ranking", "Alerta", "NOMES", "DIFERENCA_GB"]]
    .style.format({"DIFERENCA_GB": lambda x: formatar_unidade(x)}),
    use_container_width=True
)