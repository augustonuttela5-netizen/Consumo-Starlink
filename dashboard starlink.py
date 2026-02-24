import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Dashboard de Consumo")

st.title("Dashboard de Consumo - Bases e Tráfego")

# Função para converter GB/TB em float GB
def converter_para_gb(valor):
    if pd.isna(valor):
        return 0
    valor = str(valor).strip().upper().replace(" ", "")
    if "TB" in valor:
        return float(valor.replace("TB", "")) * 1024
    elif "GB" in valor:
        return float(valor.replace("GB", ""))
    else:
        return float(valor)

# -------------------
# Ler CSVs
df_bases = pd.read_csv("starlink_bases.csv", sep=",")
df_trafego = pd.read_csv("trafego_carros.csv", sep=",")

# Limpar espaços nas colunas
df_bases.columns = [c.strip() for c in df_bases.columns]
df_trafego.columns = [c.strip() for c in df_trafego.columns]

# Converter consumos para GB e calcular diferença
for df in [df_bases, df_trafego]:
    df["CONSUMO_INICIAL_GB"] = df["CONSUMO_INICIAL"].apply(converter_para_gb)
    df["CONSUMO_FINAL_GB"] = df["CONSUMO_FINAL"].apply(converter_para_gb)
    df["DIFERENCA_GB"] = df["CONSUMO_FINAL_GB"] - df["CONSUMO_INICIAL_GB"]

# -------------------
# Sidebar: escolher Bases ou Tráfego
tipo = st.sidebar.selectbox("Selecionar tipo de dado", ["Bases Starlink", "Tráfego de Carros"])

if tipo == "Bases Starlink":
    df = df_bases.copy()
    label_col = "LOCALIDADE"
else:
    df = df_trafego.copy()
    label_col = "PLACA"

# -------------------
# Ordenar do menor para o maior consumo final
df = df.sort_values("CONSUMO_FINAL_GB", ascending=True)

# -------------------
# Mostrar tabela
st.subheader(f"Consumo detalhado - {tipo}")
st.dataframe(df[["NOMES", "DATA_INICIAL", "CONSUMO_INICIAL", "DATA_FINAL", "CONSUMO_FINAL", label_col, "DIFERENCA_GB"]])

# -------------------
# Gráfico detalhado com consumo inicial e final
st.subheader(f"Gráfico detalhado de Consumo - {tipo}")

fig = go.Figure()

# Barra Consumo Inicial
fig.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["CONSUMO_INICIAL_GB"],
    name='12/02/2026',
    text=df["CONSUMO_INICIAL_GB"].apply(lambda x: f"{x:.2f} GB"),
    textposition='outside'
))

# Barra Consumo Final
fig.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["CONSUMO_FINAL_GB"],
    name='19/02/2026',
    text=df["CONSUMO_FINAL_GB"].apply(lambda x: f"{x:.2f} GB"),
    textposition='outside'
))

fig.update_layout(
    barmode='group',
    xaxis_title="NOMES",
    yaxis_title="Consumo (GB)",
    title=f"Consumo detalhado - {tipo} (12/02 vs 19/02)",
    xaxis_tickangle=-45,
    template="plotly_white",
    height=500
)

st.plotly_chart(fig, use_container_width=True)