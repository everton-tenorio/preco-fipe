import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import requests
import plotly.graph_objects as go
from datetime import datetime

app = dash.Dash(__name__)

# Função para fazer requisições à API
def req(url, data):
    return requests.post(url, data=data).json()

# URLs para API
url_api = 'https://veiculos.fipe.org.br/api/veiculos'
url_tabelaref = f'{url_api}/ConsultarTabelaDeReferencia'
url_marcas = f'{url_api}/ConsultarMarcas'
url_modelos = f'{url_api}/ConsultarModelos'
url_ano_modelos = f'{url_api}/ConsultarAnoModelo'
url_todos_parametros = f'{url_api}/ConsultarValorComTodosParametros'

# Layout do aplicativo
app.layout = html.Div([
    html.H1('Consulta FIPE'),
        
    dcc.Dropdown(id='tipo-veiculo', options=[
        {'label': 'Carro', 'value': 1},
        {'label': 'Moto', 'value': 2},
        {'label': 'Caminhão', 'value': 3}
    ], placeholder="Selecione o tipo de veículo"),
    
    dcc.Dropdown(id='marca-veiculo', placeholder="Selecione a marca"),
    
    dcc.Dropdown(id='modelo-veiculo', placeholder="Selecione o modelo"),
    
    dcc.Dropdown(id='ano-modelo', placeholder="Selecione o ano"),
    
    html.Button('Consultar', id='btn-consulta-preco', n_clicks=0),
    
    html.Div(id='preco-atual-fipe'),
    
    html.Hr(),

    html.H2('Consultar Variação de Preço'),
    html.Label('Selecione o ano:', id='label-select'),
    html.Div([
        dcc.Dropdown(id='ano-consulta', placeholder="Selecione o ano"),
        html.Button('Consultar', id='btn-consulta-variacao', n_clicks=0),
    ], className="select-variant"),
    
    dcc.Graph(id='grafico-preco'),  

    html.Div([
        html.A(
                html.Div([
                    html.Img(
                    id="github-img",
                    width="15px",
                    src="./assets/github.png"),
                    html.Small(" Criado por Everton Tenorio"),
                ], className="github"),
                href="https://github.com/everton-tenorio/preco-fipe",
                target="_blank",       
        )
    ]),

])

# Callback para popular o dropdown do ano
@app.callback(
    Output('ano-consulta', 'options'),
    Input('btn-consulta-preco', 'n_clicks')
)
def populate_year_dropdown(n_clicks):
    referencias = req(url_tabelaref, '')
    anos = sorted({referencia['Mes'].split('/')[-1].strip() for referencia in referencias}, reverse=True)
    return [{'label': ano, 'value': ano} for ano in anos]

# Callback para atualizar as marcas de veículos com base no tipo de veículo selecionado
@app.callback(
    Output('marca-veiculo', 'options'),
    Input('tipo-veiculo', 'value')
)
def update_marcas(tipo_veiculo):
    if tipo_veiculo is None:
        return []
    referencias = req(url_tabelaref, '')
    dados_veiculo_marca = {
        'codigoTabelaReferencia': referencias[0]['Codigo'],
        'codigoTipoVeiculo': tipo_veiculo
    }
    marcas = req(url_marcas, dados_veiculo_marca)
    return [{'label': marca['Label'], 'value': marca['Value']} for marca in marcas]

# Callback para atualizar os modelos de veículos com base na marca selecionada
@app.callback(
    Output('modelo-veiculo', 'options'),
    Input('marca-veiculo', 'value'),
    State('tipo-veiculo', 'value')
)
def update_modelos(marca, tipo_veiculo):
    if marca is None:
        return []
    referencias = req(url_tabelaref, '')
    dados_veiculo_modelo = {
        'codigoTabelaReferencia': referencias[0]['Codigo'],
        'codigoTipoVeiculo': tipo_veiculo,
        'codigoMarca': marca
    }
    modelos = req(url_modelos, dados_veiculo_modelo)['Modelos']
    return [{'label': modelo['Label'], 'value': modelo['Value']} for modelo in modelos]

# Callback para atualizar os anos dos modelos de veículos com base no modelo selecionado
@app.callback(
    Output('ano-modelo', 'options'),
    Input('modelo-veiculo', 'value'),
    State('tipo-veiculo', 'value'),
    State('marca-veiculo', 'value')
)
def update_anos(modelo, tipo_veiculo, marca):
    if modelo is None:
        return []
    referencias = req(url_tabelaref, '')
    dados_veiculos_ano_modelo = {
        'codigoTabelaReferencia': referencias[0]['Codigo'],
        'codigoTipoVeiculo': tipo_veiculo,
        'codigoMarca': marca,
        'codigoModelo': modelo
    }
    anos = req(url_ano_modelos, dados_veiculos_ano_modelo)
    return [{'label': ano['Label'], 'value': ano['Value']} for ano in anos]

# Callback para consultar o preço atual e exibir
@app.callback(
    Output('preco-atual-fipe', 'children'),
    Input('btn-consulta-preco', 'n_clicks'),
    State('ano-modelo', 'value'),
    State('modelo-veiculo', 'value'),
    State('marca-veiculo', 'value'),
    State('tipo-veiculo', 'value')
)
def consultar_preco_atual(n_clicks, ano, modelo, marca, tipo):
    if n_clicks == 0:
        return ''
    referencias = req(url_tabelaref, '')
    ano_modelo, codigo_tipo_combustivel = ano.split('-')
    dados_veiculos_ano_modelo = {
        'codigoTabelaReferencia': referencias[0]['Codigo'],
        'codigoTipoVeiculo': tipo,
        'codigoMarca': marca,
        'codigoModelo': modelo,
        'ano': ano,
        'anoModelo': ano_modelo,
        'codigoTipoCombustivel': codigo_tipo_combustivel,
        'tipoConsulta': 'tradicional'
    }
    response = req(url_todos_parametros, dados_veiculos_ano_modelo)

    return html.Div([
        html.Li(f"Preço Atual: {response['Valor']}"),
        html.Li(f"Código FIPE: {response['CodigoFipe']}"),
        html.Li(f"Mês de referência: {response['MesReferencia']}"),
        html.Li(f"Marca: {response['Marca']}"),
        html.Li(f"Modelo: {response['Modelo']}"),
        html.Li(f"Ano: {response['AnoModelo']}"),
        html.Li(f"Combustível: {response['Combustivel']}"),
        html.Li(f"Data da consulta: {response['DataConsulta']}"),
])

# Callback para gerar o gráfico de variação de preço
@app.callback(
    Output('grafico-preco', 'figure'),
    Input('btn-consulta-variacao', 'n_clicks'),
    State('ano-consulta', 'value'),
    State('ano-modelo', 'value'),
    State('modelo-veiculo', 'value'),
    State('marca-veiculo', 'value'),
    State('tipo-veiculo', 'value')
)
def consultar_variacao_preco(n_clicks, ano_consulta, ano, modelo, marca, tipo):
    if n_clicks == 0:
        return go.Figure()
    
    referencias = req(url_tabelaref, '')
    referencias_ano = [ref for ref in referencias if ref['Mes'].split('/')[1].strip() == ano_consulta]
    
    meses = []
    precos = []
    for referencia in referencias_ano[::-1]:
        codigo_tabela_referencia = referencia['Codigo']
        ano_modelo, codigo_tipo_combustivel = ano.split('-')
        dados_veiculos_ano_modelo = {
            'codigoTabelaReferencia': codigo_tabela_referencia,
            'codigoTipoVeiculo': tipo,
            'codigoMarca': marca,
            'codigoModelo': modelo,
            'ano': ano,
            'anoModelo': ano_modelo,
            'codigoTipoCombustivel': codigo_tipo_combustivel,
            'tipoConsulta': 'tradicional'
        }
        response = req(url_todos_parametros, dados_veiculos_ano_modelo)
        preco_str = response['Valor'].replace('R$ ', '').replace('.', '').replace(',', '.')
        preco = float(preco_str)
        meses.append(referencia['Mes'])
        precos.append(preco)
    
    fig = go.Figure(data=go.Scatter(x=meses, y=precos, mode='lines+markers'))
    fig.update_layout(
        title=f'{response["Modelo"]} - Variação de Preço por Mês',
        xaxis_title='Mês',
        yaxis_title='Preço (R$)',
        xaxis=dict(type='category'),
        width=500,
    )
    return fig

if __name__ == '__main__':
    app.run_server(host="0.0.0.0")
