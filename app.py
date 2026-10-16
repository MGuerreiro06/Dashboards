"""
Dashboard do E-commerce - Aplicação Dash
Execute com:  python app.py
Depois acesse o link exibido no terminal (padrão: http://127.0.0.1:8050)
"""

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# ---------------------------------------------------------------------------
# 1. Leitura dos dados
# ---------------------------------------------------------------------------
df = pd.read_csv("ecommerce_estatistica.csv", encoding="utf-8")
df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")

# Colunas numéricas usadas na correlação (apenas as originais, sem as normalizadas/codificadas)
COLS_NUM = ["Nota", "N_Avaliações", "Desconto", "Preço", "Qtd_Vendidos_Cod"]
COLS_NUM = [c for c in COLS_NUM if c in df.columns]

marcas = sorted(df["Marca"].dropna().unique())
generos = sorted(df["Gênero"].dropna().unique())
materiais = sorted(df["Material"].dropna().unique())

# ---------------------------------------------------------------------------
# 2. Layout
# ---------------------------------------------------------------------------
app = Dash(__name__)
app.title = "Dashboard E-commerce"
server = app.server  # necessário para o gunicorn em produção (gunicorn app:server)

CARD = {
    "background": "white",
    "borderRadius": "10px",
    "padding": "10px",
    "boxShadow": "0 1px 4px rgba(0,0,0,0.12)",
}

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "background": "#f2f4f8", "padding": "20px"},
    children=[
        html.H1("Dashboard de Análise do E-commerce", style={"textAlign": "center"}),
        html.P(
            "Explore as distribuições, relações e comparações entre os produtos. "
            "Use os filtros para refinar a análise.",
            style={"textAlign": "center", "color": "#555"},
        ),
        # ------------------------- Filtros -------------------------
        html.Div(
            style={**CARD, "display": "grid",
                   "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
                   "gap": "15px", "marginBottom": "20px"},
            children=[
                html.Div([
                    html.Label("Marca"),
                    dcc.Dropdown(marcas, multi=True, id="f-marca", placeholder="Todas as marcas"),
                ]),
                html.Div([
                    html.Label("Gênero"),
                    dcc.Dropdown(generos, multi=True, id="f-genero", placeholder="Todos os gêneros"),
                ]),
                html.Div([
                    html.Label("Material"),
                    dcc.Dropdown(materiais, multi=True, id="f-material", placeholder="Todos os materiais"),
                ]),
                html.Div([
                    html.Label("Faixa de preço"),
                    dcc.RangeSlider(
                        id="f-preco",
                        min=float(df["Preço"].min()),
                        max=float(df["Preço"].max()),
                        value=[float(df["Preço"].min()), float(df["Preço"].max())],
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ]),
            ],
        ),
        html.Div(id="kpis", style={"display": "flex", "gap": "15px", "marginBottom": "20px",
                                   "flexWrap": "wrap"}),
        # ------------------------- Gráficos -------------------------
        html.Div(
            style={"display": "grid",
                   "gridTemplateColumns": "repeat(auto-fit, minmax(480px, 1fr))",
                   "gap": "20px"},
            children=[
                html.Div(dcc.Graph(id="g-hist-nota"), style=CARD),
                html.Div(dcc.Graph(id="g-hist-preco"), style=CARD),
                html.Div(dcc.Graph(id="g-disp"), style=CARD),
                html.Div(dcc.Graph(id="g-heatmap"), style=CARD),
                html.Div(dcc.Graph(id="g-barras"), style=CARD),
                html.Div(dcc.Graph(id="g-pizza"), style=CARD),
                html.Div(dcc.Graph(id="g-box"), style=CARD),
                html.Div(dcc.Graph(id="g-densidade"), style=CARD),
            ],
        ),
    ],
)


# ---------------------------------------------------------------------------
# 3. Callback único: aplica filtros e atualiza todos os gráficos
# ---------------------------------------------------------------------------
def kpi(titulo, valor):
    return html.Div(
        [html.Div(titulo, style={"color": "#666", "fontSize": "13px"}),
         html.Div(valor, style={"fontSize": "24px", "fontWeight": "bold"})],
        style={**CARD, "minWidth": "180px", "flex": "1", "textAlign": "center"},
    )


def figura_vazia(titulo):
    fig = px.scatter(title=titulo)
    fig.add_annotation(text="Sem dados para os filtros selecionados",
                       showarrow=False, font={"size": 14})
    return fig


@app.callback(
    [Output("kpis", "children"),
     Output("g-hist-nota", "figure"),
     Output("g-hist-preco", "figure"),
     Output("g-disp", "figure"),
     Output("g-heatmap", "figure"),
     Output("g-barras", "figure"),
     Output("g-pizza", "figure"),
     Output("g-box", "figure"),
     Output("g-densidade", "figure")],
    [Input("f-marca", "value"),
     Input("f-genero", "value"),
     Input("f-material", "value"),
     Input("f-preco", "value")],
)
def atualizar(marca, genero, material, faixa_preco):
    d = df.copy()
    if marca:
        d = d[d["Marca"].isin(marca)]
    if genero:
        d = d[d["Gênero"].isin(genero)]
    if material:
        d = d[d["Material"].isin(material)]
    if faixa_preco:
        d = d[d["Preço"].between(faixa_preco[0], faixa_preco[1])]

    if d.empty:
        vazias = [figura_vazia(t) for t in
                  ["Histograma de Notas", "Histograma de Preços", "Nota x Preço",
                   "Correlação", "Preço médio por marca", "Distribuição por material",
                   "Preço por gênero", "Densidade das notas"]]
        return [kpi("Produtos", "0")] + vazias

    # KPIs
    kpis = [
        kpi("Produtos", f"{len(d)}"),
        kpi("Nota média", f"{d['Nota'].mean():.2f}"),
        kpi("Preço médio", f"R$ {d['Preço'].mean():.2f}"),
        kpi("Desconto médio", f"{d['Desconto'].mean():.1f}%"),
    ]

    # Histogramas
    fig_nota = px.histogram(d, x="Nota", nbins=20, title="Distribuição das Notas",
                            color_discrete_sequence=["#3b82f6"])
    fig_preco = px.histogram(d, x="Preço", nbins=30, title="Distribuição dos Preços",
                             color_discrete_sequence=["#10b981"])

    # Dispersão Nota x Preço (com linha de tendência OLS, se statsmodels estiver disponível)
    try:
        fig_disp = px.scatter(d, x="Preço", y="Nota", color="Gênero", size="N_Avaliações",
                              hover_name="Título", trendline="ols" if len(d) > 2 else None,
                              trendline_scope="overall",
                              title="Relação entre Preço e Nota")
    except Exception:
        fig_disp = px.scatter(d, x="Preço", y="Nota", color="Gênero", size="N_Avaliações",
                              hover_name="Título", title="Relação entre Preço e Nota")

    # Mapa de calor das correlações
    corr = d[COLS_NUM].corr()
    fig_heat = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                         zmin=-1, zmax=1, title="Mapa de Calor das Correlações")

    # Barras: preço médio por marca (top 15)
    top = (d.groupby("Marca")["Preço"].mean().sort_values(ascending=False).head(15)
           .reset_index())
    fig_bar = px.bar(top, x="Marca", y="Preço", title="Preço Médio por Marca (Top 15)",
                     color="Preço", color_continuous_scale="Viridis")

    # Pizza: distribuição por material (top 8 + outros)
    mat = d["Material"].value_counts()
    if len(mat) > 8:
        mat = pd.concat([mat.head(8), pd.Series({"Outros": mat.iloc[8:].sum()})])
    fig_pie = px.pie(values=mat.values, names=mat.index, title="Distribuição por Material")

    # Boxplot: preço por gênero
    fig_box = px.box(d, x="Gênero", y="Preço", color="Gênero", title="Preço por Gênero")

    # Densidade das notas por gênero (histograma normalizado com marginal)
    fig_dens = px.histogram(d, x="Nota", color="Gênero", histnorm="probability density",
                            barmode="overlay", opacity=0.6, marginal="rug",
                            title="Densidade das Notas por Gênero")

    return [kpis, fig_nota, fig_preco, fig_disp, fig_heat, fig_bar, fig_pie, fig_box, fig_dens]


# ---------------------------------------------------------------------------
# 4. Execução
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    app.run(debug=os.environ.get("DEBUG", "0") == "1", port=int(os.environ.get("PORT", 8050)))
