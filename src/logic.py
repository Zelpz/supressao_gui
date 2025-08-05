import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
import os

def carregar_dados(caminho_gpkg, shp_fazenda):
    desmatamento = gpd.read_file(caminho_gpkg)
    fazenda = gpd.read_file(shp_fazenda)
    return desmatamento, fazenda

def filtrar_por_periodo(df, ano_inicio, ano_fim):
    # Procura por qualquer coluna que comece com 'year'
    year_col = None
    for col in df.columns:
        if col.lower().startswith("year"):
            year_col = col
            break
    if year_col is None:
        raise KeyError(f"Nenhuma coluna 'year' encontrada. Colunas disponíveis: {list(df.columns)}")
    return df[(df[year_col] >= ano_inicio) & (df[year_col] <= ano_fim)]
    

def calcular_area_intersecao(desmatamento, fazenda):
    # Filtra apenas Polygon e MultiPolygon
    desmatamento = desmatamento[desmatamento.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
    fazenda = fazenda[fazenda.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
    intersecao = gpd.overlay(desmatamento, fazenda, how='intersection', keep_geom_type=False)
    intersecao['area_km'] = intersecao.geometry.area / 10_000
    return intersecao

def calcular_percentual(intersecao, area_fazenda):
    area_total_desmatada = intersecao['area_km'].sum()
    percentual = (area_total_desmatada / area_fazenda) * 100
    return percentual, area_total_desmatada

def processar_periodos(desmatamento, fazenda):
    periodos = {
        "1980_1994": (1980, 1994),
        "1994_2008": (1995, 2008),
        "2008_2020": (2009, 2020),
        "2020_2025": (2021, 2025)
    }

    resultados = []
    area_total_fazenda = fazenda.geometry.area.sum() / 10_000

    for nome_periodo, (inicio, fim) in periodos.items():
        filtrado = filtrar_por_periodo(desmatamento, inicio, fim)
        intersecao = calcular_area_intersecao(filtrado, fazenda)
        percentual, area = calcular_percentual(intersecao, area_total_fazenda)
        
        intersecao['periodo'] = nome_periodo
        intersecao['percentual'] = percentual
        intersecao['area_periodo'] = area
        intersecao['area_total_fazenda'] = area_total_fazenda

        resultados.append(intersecao)

    resultado_df = pd.concat(resultados, ignore_index=True)
    # Remove geometrias que não são Polygon/MultiPolygon
    resultado_df = resultado_df[resultado_df.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
    # Converter colunas datetime para string para evitar erro de serialização
    for col in resultado_df.columns:
        if pd.api.types.is_datetime64_any_dtype(resultado_df[col]):
            resultado_df[col] = resultado_df[col].astype(str)
    return gpd.GeoDataFrame(resultado_df)