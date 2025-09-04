import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 1. Ler a base direto do Google Sheets
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTnWwzZf1Tcz234z8kzSWK9BrR48orq8VfPV0s9J9Vv711UEI6U4CrwqouXM9pbb-5UKSZBHPuDMRnr/pub?gid=90608747&single=true&output=csv"
df = pd.read_csv(url)

# 2. Tratar colunas numéricas
colunas_numericas = ["Meta Mínima",
                     "Meta Básica", "Meta Master", "Faturamento"]

for col in colunas_numericas:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 3. Paletas de cores por time
paletas_times = {
    "CIS": {
        "metas": ["#FFE7B3", "#FFD066", "#FFA90A"],
        "faturamento": "#100774"
    },
    "GGB": {
        "metas": ["#f9c7ce", "#de96a0", "#ca6674"],
        "faturamento": "#631515"
    },
    "Novos Negócios": {
        "metas": ["#d6d9e2", "#b3b9c8", "#969eb0"],
        "faturamento": "#96000b"
    },
    "Canal ED": {
        "metas": ["#99e6d1", "#3ce6ad", "#04d685"],
        "faturamento": "#ff3c72"
    },
    "Grandes Eventos": {
        "metas": ["#A9F7C9", "#53F68D", "#04F167"],
        "faturamento": "#0a3d91"
    }
}

# Definir espaçamento automático (dtick)


def calcular_dtick(valor_max):
    if valor_max <= 100_000:
        return 20_000
    elif valor_max <= 300_000:
        return 50_000
    elif valor_max <= 1_000_000:
        return 100_000
    else:
        return 200_000

# 5. Função principal


def plot_time(time_nome):
    df_time = df[df["Time"].str.strip().str.upper() ==
                 time_nome.strip().upper()]

    if df_time.empty:
        st.warning(f"⚠️ Nenhum consultor encontrado para o time '{time_nome}'")
        return None

    df_time = df_time.sort_values(
        by="Faturamento", ascending=False).reset_index(drop=True)
    df_time["Vendedor"] = df_time["Vendedor"].apply(lambda x: x + " ")

    cores_metas = paletas_times.get(time_nome, paletas_times["CIS"])["metas"]
    cor_faturamento = paletas_times.get(
        time_nome, paletas_times["CIS"])["faturamento"]

    fig = go.Figure()

    for i, row in df_time.iterrows():
        vendedor = row["Vendedor"]
        metas = [row["Meta Mínima"], row["Meta Básica"], row["Meta Master"]]
        metas_diff = [metas[0], metas[1]-metas[0], metas[2]-metas[1]]
        nomes_metas = ["Meta Mínima", "Meta Básica", "Meta Master"]

        for j, (meta_val, nome) in enumerate(zip(metas_diff, nomes_metas)):
            fig.add_trace(go.Bar(
                x=[meta_val],
                y=[vendedor],
                orientation="h",
                marker=dict(color=cores_metas[j]),
                name=nome,
                showlegend=(i == 0),
                hovertemplate=f'R$ {metas[j]:,.2f}'.replace(',', 'X').replace(
                    '.', ',').replace('X', '.') + "<extra></extra>"
            ))

    max_valor = df_time[["Meta Master", "Faturamento"]].values.max()
    limite_x = max_valor * 1.25
    dtick_valor = calcular_dtick(limite_x)

    for i, row in df_time.iterrows():
        vendedor = row["Vendedor"]
        faturamento = row["Faturamento"]
        perc_meta = faturamento / \
            row["Meta Master"] * 100 if row["Meta Master"] > 0 else 0

        fig.add_trace(go.Scatter(
            x=[0, faturamento],
            y=[vendedor, vendedor],
            mode="lines",
            line=dict(color=cor_faturamento, width=6),
            name="Faturamento",
            showlegend=(i == 0),
            hovertemplate=f'Faturamento: R$ {faturamento:,.2f} ({perc_meta:.0f}%)'.replace(
                ',', 'X').replace('.', ',').replace('X', '.')
        ))

        # sempre usar a cor da linha
        cor_texto = cor_faturamento

        if faturamento >= limite_x * 0.75:
            posicao_texto = "top center"
        else:
            posicao_texto = "middle right"

        fig.add_trace(go.Scatter(
            x=[faturamento],
            y=[vendedor],
            mode="markers+text",
            marker=dict(color=cor_faturamento, size=13, symbol="circle"),
            text=[f"<b>R$ {faturamento:,.2f} ({perc_meta:.0f}%)</b>".replace(
                ',', 'X').replace('.', ',').replace('X', '.')],
            textposition=posicao_texto,
            textfont=dict(color=cor_texto, size=17),
            showlegend=False
        ))

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=f"Faturamento vs Metas – Time {time_nome}",
            font=dict(size=18, family="Arial", color="black")
        ),
        xaxis=dict(
            title="Valores (R$)",
            showgrid=True,
            gridcolor="#EDEDED",
            range=[0, limite_x],
            dtick=dtick_valor,
            tickformat=","
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=15)
        ),

        legend=dict(
            font=dict(size=16)
        ),

        bargap=0.45,
        template="plotly_white",

        # 🔹 Ajuste da posição/estilo do balão
        hovermode="closest",
        hoverlabel=dict(
            align="left",
            font=dict(size=12, color="black"),
            bgcolor="white",
            bordercolor="black"
        )
    )

    return fig


st.set_page_config(page_title="Acompanhamento Comercial SJC", layout="wide")

# título
st.title("📊 Acompanhamento Comercial SJC")

# seletor na barra lateral
esteiras = ["CIS", "Canal ED", "GGB", "Grandes Eventos", "Novos Negócios"]
time_escolhido = st.sidebar.selectbox("Selecione a esteira:", esteiras)

# gera o gráfico para a esteira selecionada
fig = plot_time(time_escolhido)
if fig:
    st.plotly_chart(fig, use_container_width=True)
