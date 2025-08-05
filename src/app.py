import streamlit as st
import geopandas as gpd
from logic import processar_periodos
import pydeck as pdk
import tempfile
import os
import pandas as pd
import shutil

st.title("Supressão - Análise de Desmatamento")

def save_uploaded_file(uploadedfile, suffix):
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, f"input{suffix}")
    with open(file_path, "wb") as f:
        f.write(uploadedfile.read())
    return file_path, temp_dir

def save_shapefile(files):
    temp_dir = tempfile.mkdtemp()
    paths = {}
    for f in files:
        ext = os.path.splitext(f.name)[1]
        path = os.path.join(temp_dir, f"input{ext}")
        with open(path, "wb") as out:
            out.write(f.read())
        paths[ext] = path
    return paths, temp_dir

def sanitize_columns(gdf):
    for col in gdf.columns:
        if col != "geometry":
            gdf[col] = gdf[col].apply(lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x))
    return gdf

# Upload da camada de desmatamento
desmatamento_files = st.file_uploader(
    "Selecione os arquivos SHP (mínimo: .shp, .shx, .dbf) ou 1 GPKG da área de desmatamento", 
    type=["gpkg", "shp", "shx", "dbf", "prj"],
    accept_multiple_files=True
)

# Upload da camada da fazenda
fazenda_files = st.file_uploader(
    "Selecione os arquivos SHP (mínimo: .shp, .shx, .dbf) ou 1 GPKG da área da fazenda", 
    type=["gpkg", "shp", "shx", "dbf", "prj"],
    accept_multiple_files=True
)

if st.button("Executar Análise"):
    if not desmatamento_files or not fazenda_files:
        st.error("Por favor, envie os arquivos necessários para desmatamento e fazenda.")
        st.stop()

    # ====================
    # Processa desmatamento
    # ====================
    if len(desmatamento_files) == 1 and desmatamento_files[0].name.endswith(".gpkg"):
        gpkg_path, _ = save_uploaded_file(desmatamento_files[0], ".gpkg")
        desmatamento = gpd.read_file(gpkg_path)
    elif len(desmatamento_files) >= 3 and any(f.name.endswith(".shp") for f in desmatamento_files):
        shp_paths, _ = save_shapefile(desmatamento_files)
        desmatamento = gpd.read_file(shp_paths[".shp"])
    else:
        st.error("Arquivos de desmatamento inválidos. Envie um único .gpkg ou os arquivos .shp, .shx e .dbf.")
        st.stop()

    # ====================
    # Processa fazenda
    # ====================
    if len(fazenda_files) == 1 and fazenda_files[0].name.endswith(".gpkg"):
        gpkg_path, _ = save_uploaded_file(fazenda_files[0], ".gpkg")
        fazenda = gpd.read_file(gpkg_path)
    elif len(fazenda_files) >= 3 and any(f.name.endswith(".shp") for f in fazenda_files):
        shp_paths, _ = save_shapefile(fazenda_files)
        fazenda = gpd.read_file(shp_paths[".shp"])
    else:
        st.error("Arquivos da fazenda inválidos. Envie um único .gpkg ou os arquivos .shp, .shx e .dbf.")
        st.stop()

    st.success("Arquivos carregados com sucesso!")

    # Interseção espacial
    desmatamento_intersect = gpd.overlay(desmatamento, fazenda, how='intersection', keep_geom_type=False)
    resultado = processar_periodos(desmatamento_intersect, fazenda)

    
    st.write("Resultado da análise:")
    st.dataframe(resultado[["periodo", "year","area_km", "percentual", "area_periodo", "area_total_fazenda"]])
    # Sanitiza colunas para evitar erro de serialização
    resultado = sanitize_columns(resultado)
    fazenda = sanitize_columns(fazenda)

    # Reprojeção para EPSG:4326 antes do mapa
    if resultado.crs is not None and resultado.crs.to_epsg() != 4326:
        resultado = resultado.to_crs(epsg=4326)
    if fazenda.crs is not None and fazenda.crs.to_epsg() != 4326:
        fazenda = fazenda.to_crs(epsg=4326)

    # Verificações antes do mapa
    if resultado.empty:
        st.warning("O resultado está vazio. Verifique os dados de entrada e os filtros aplicados.")
        st.stop()
    if not resultado.is_valid.all():
        st.warning("Há geometrias inválidas no resultado. Corrija os dados de entrada.")
        st.stop()
    if resultado.geometry.is_empty.all():
        st.warning("Todas as geometrias do resultado estão vazias.")
        st.stop()
    if fazenda.empty or fazenda.geometry.is_empty.all():
        st.warning("O arquivo da fazenda está vazio ou sem geometrias válidas.")
        st.stop()
    resultado = resultado[resultado.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
    fazenda = fazenda[fazenda.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()

    # pydeck: exibe o resultado no mapa
    geojson_resultado = resultado.__geo_interface__
    geojson_fazenda = fazenda.__geo_interface__

    layers = [
        pdk.Layer(
            "GeoJsonLayer",
            geojson_resultado,
            pickable=True,
            stroked=True,
            filled=True,
            get_fill_color=[255, 0, 0, 80],
            get_line_color=[255, 0, 0, 255],
            line_width_min_pixels=1,
        ),
        pdk.Layer(
            "GeoJsonLayer",
            geojson_fazenda,
            pickable=True,
            stroked=True,
            filled=False,
            get_line_color=[0, 155, 0, 255],
            line_width_min_pixels=2,
        ),
    ]

    centro_y = resultado.geometry.centroid.y.mean()
    centro_x = resultado.geometry.centroid.x.mean()
    view_state = pdk.ViewState(
        longitude=centro_x,
        latitude=centro_y,
        zoom=12,
        pitch=0,
    )

    r = pdk.Deck(layers=layers, initial_view_state=view_state)
    st.pydeck_chart(r)

    # Download CSV
    csv = resultado.drop(columns="geometry").to_csv(index=False).encode("utf-8")
    st.download_button("Baixar resultado CSV", csv, "resultado.csv", "text/csv")

    # Download SHP (compactado em ZIP)
    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = os.path.join(tmpdir, "resultado.shp")
        resultado.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")
        # Compacta todos os arquivos do shapefile em um zip
        zip_path = shutil.make_archive(
            base_name=os.path.join(tmpdir, "resultado_shp"),
            format='zip',
            root_dir=tmpdir,
            base_dir="."
        )
        with open(zip_path, "rb") as f:
            st.download_button(
                label="Baixar resultado SHP (ZIP)",
                data=f,
                file_name="resultado_shp.zip",
                mime="application/zip"
            )