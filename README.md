# Supressão GUI 🌱

Uma interface interativa em **Streamlit** para análise de desmatamento acumulado ao longo de períodos históricos em áreas delimitadas por shapefiles, utilizando dados públicos do TerraBrasilis/PRODES para testes.

## 📌 Funcionalidades

- Upload de shapefiles (.shp) e camadas Geopackage (.gpkg)
- Cálculo automático de percentuais de desmatamento da área por períodos:
  - 1980–1994
  - 1994–2008
  - 2008–2020
  - 2020–2024/2025
- Visualização dos resultados com mapas e tabelas
- Exportação dos dados processados em formato CSV

## ⚙️ Tecnologias

- [Streamlit](https://streamlit.io/)
- [GeoPandas](https://geopandas.org/)
- [Shapely](https://shapely.readthedocs.io/)
- [Pandas](https://pandas.pydata.org/)
- [Pydeck](https://deckgl.readthedocs.io/)

## ▶️ Como usar

1. Clone o repositório:

git clone https://github.com/seu-usuario/supressao-gui.git
cd supressao-gui

2. Instale as dependências

pip install -r requirements.txt

3. Rode a aplicação

streamlit run src/app.py

## 🛰️ Dados
Os dados de desmatamento utilizados são públicos e podem ser baixados do portal TerraBrasilis.

## ⚠️ Observação importante
Este projeto foi desenvolvido com base nos dados do PRODES fornecidos pelo portal TerraBrasilis. As colunas esperadas para o funcionamento correto são:

area_km (área do polígono em km²)

year (ano de ocorrência do desmatamento)

Caso seus dados tenham colunas com nomes diferentes, será necessário adaptar o código para refletir os novos nomes de atributos.
