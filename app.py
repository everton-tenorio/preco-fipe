from dash import Dash, dcc, html, Output, Input, State
from request_all import req
import plotly.graph_objects as go

# URLs para API
url_api = 'https://veiculos.fipe.org.br/api/veiculos'
url_tabelaref = f'{url_api}/ConsultarTabelaDeReferencia'
url_marcas = f'{url_api}/ConsultarMarcas'
url_modelos = f'{url_api}/ConsultarModelos'
url_ano_modelos = f'{url_api}/ConsultarAnoModelo'
url_todos_parametros = f'{url_api}/ConsultarValorComTodosParametros'


class FIPEPrice:
    def __init__(self):
        self.__app = Dash(
            __name__,
            title="Preço FIPE",
            update_title="Carregando...",
            use_pages=False, 
        )

        # Configuração inicial e callbacks
        self.referencias_anos = req(url_tabelaref, '')
        self.referencias = self.referencias_anos[0]['Codigo']
        self.set_callbacks()
        self.set_layout()

    @property
    def app(self):
        return self.__app

    def set_layout(self):
        self.app.layout = html.Div([
            html.H1('Preço FIPE'),
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
                
            dcc.Loading(
                id='loading-1',
                type='default',
                children=[dcc.Graph(id='grafico-preco'),],
                fullscreen=False
            ),    
            
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

    def set_callbacks(self):
        @self.app.callback(
            Output('ano-consulta', 'options'),
            Input('btn-consulta-preco', 'n_clicks')
        )
        def populate_year_dropdown(n_clicks):
            anos = sorted({referencia['Mes'].split('/')[-1].strip() for referencia in self.referencias_anos}, reverse=True)
            return [{'label': ano, 'value': ano} for ano in anos]

        @self.app.callback(
            Output('marca-veiculo', 'options'),
            Input('tipo-veiculo', 'value')
        )
        def update_marcas(tipo_veiculo):
            if tipo_veiculo is None:
                return []
            dados_veiculo_marca = {
                'codigoTabelaReferencia': self.referencias,
                'codigoTipoVeiculo': tipo_veiculo
            }
            marcas = req(url_marcas, dados_veiculo_marca)
            return [{'label': marca['Label'], 'value': marca['Value']} for marca in marcas]

        @self.app.callback(
            Output('modelo-veiculo', 'options'),
            Input('marca-veiculo', 'value'),
            State('tipo-veiculo', 'value')
        )
        def update_modelos(marca, tipo_veiculo):
            if marca is None:
                return []
            dados_veiculo_modelo = {
                'codigoTabelaReferencia': self.referencias,
                'codigoTipoVeiculo': tipo_veiculo,
                'codigoMarca': marca
            }
            modelos = req(url_modelos, dados_veiculo_modelo)['Modelos']
            return [{'label': modelo['Label'], 'value': modelo['Value']} for modelo in modelos]

        @self.app.callback(
            Output('ano-modelo', 'options'),
            Input('modelo-veiculo', 'value'),
            State('tipo-veiculo', 'value'),
            State('marca-veiculo', 'value')
        )
        def update_anos(modelo, tipo_veiculo, marca):
            if modelo is None:
                return []
            dados_veiculos_ano_modelo = {
                'codigoTabelaReferencia': self.referencias,
                'codigoTipoVeiculo': tipo_veiculo,
                'codigoMarca': marca,
                'codigoModelo': modelo
            }
            anos = req(url_ano_modelos, dados_veiculos_ano_modelo)
            return [{'label': ano['Label'], 'value': ano['Value']} for ano in anos]

        @self.app.callback(
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
            ano_modelo, codigo_tipo_combustivel = ano.split('-')
            dados_veiculos_ano_modelo = {
                'codigoTabelaReferencia': self.referencias,
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

        @self.app.callback(
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
            
            referencias_ano = [ref for ref in self.referencias_anos if ref['Mes'].split('/')[1].strip() == ano_consulta]
            
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
                title=f'Variação de Preço por Mês<br><sup>{response["Modelo"]} {response["AnoModelo"]}<br><sup>https://preco-fipe.vercel.app</sup></sup>',
                xaxis_title='Mês',
                yaxis_title='Preço (R$)',
                xaxis=dict(type='category'),
            )
            return fig


Application = FIPEPrice()
app = Application.app.server

if __name__ == "__main__":
    Application.app.run(debug=True, host="127.0.0.1")
