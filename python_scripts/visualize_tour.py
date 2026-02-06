# -*- coding: utf-8 -*-
"""
TSP Tour Visualization for Concorde
=====================================
Displays the TSP tour on an interactive map with total distance calculation.
Parses Concorde .sol output format.

(c) 2026 iM@Des - Tous droits reserves
"""

import pandas as pd
import folium
from folium import plugins
import os
from math import radians, sin, cos, sqrt, atan2

EARTH_RADIUS_M = 6371008.8


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in meters."""
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return EARTH_RADIUS_M * c


def parse_concorde_sol(sol_path):
    """Parse Concorde .sol file to get tour order (0-indexed)."""
    tour_order = []
    
    with open(sol_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        return []
    
    # First line: number of cities
    # Rest: tour indices
    for line in lines[1:]:
        parts = line.strip().split()
        for part in parts:
            try:
                tour_order.append(int(part))
            except ValueError:
                continue
    
    return tour_order


def load_data(data_path, id_col='commune', lat_col='Y-coordinate', lon_col='X-coordinate'):
    """Load data from Excel or CSV file."""
    ext = os.path.splitext(data_path)[1].lower()
    
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(data_path)
    elif ext == '.csv':
        df = pd.read_csv(data_path)
    else:
        raise ValueError(f"Format non supporte: {ext}")
    
    # Auto-detect columns
    if lat_col not in df.columns:
        for col in df.columns:
            if 'lat' in col.lower() or col.lower() == 'y' or 'y-coord' in col.lower():
                lat_col = col
                break
    
    if lon_col not in df.columns:
        for col in df.columns:
            if 'lon' in col.lower() or col.lower() == 'x' or 'x-coord' in col.lower():
                lon_col = col
                break
    
    return df, id_col, lat_col, lon_col


def create_tour_map(df, tour_order, id_col, lat_col, lon_col, output_path):
    """Create an interactive map with the tour path."""
    
    # Get coordinates in tour order
    tour_coords = []
    tour_ids = []
    
    for node_id in tour_order:
        # Concorde uses 0-indexed
        if 0 <= node_id < len(df):
            lat = df.iloc[node_id][lat_col]
            lon = df.iloc[node_id][lon_col]
            commune_id = df.iloc[node_id][id_col]
            tour_coords.append((lat, lon))
            tour_ids.append(commune_id)
    
    if not tour_coords:
        print("[ERREUR] Aucune coordonnee trouvee")
        return 0
    
    # Close the loop
    tour_coords.append(tour_coords[0])
    tour_ids.append(tour_ids[0])
    
    # Calculate total distance
    total_distance = 0.0
    for i in range(len(tour_coords) - 1):
        lat1, lon1 = tour_coords[i]
        lat2, lon2 = tour_coords[i + 1]
        total_distance += haversine_distance(lat1, lon1, lat2, lon2)
    
    total_distance_km = total_distance / 1000.0
    
    print(f"\n{'='*60}")
    print(f"RESULTATS TSP CONCORDE - VISUALISATION CARTE")
    print(f"{'='*60}")
    print(f"\nNombre de villes: {len(tour_order)}")
    print(f"Distance totale: {total_distance_km:,.2f} km")
    print(f"Distance moyenne: {total_distance_km / len(tour_order):,.2f} km")
    
    # Calculate map center
    center_lat = sum(c[0] for c in tour_coords[:-1]) / len(tour_coords[:-1])
    center_lon = sum(c[1] for c in tour_coords[:-1]) / len(tour_coords[:-1])
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; 
                background-color: white; 
                border: 2px solid #d4af37;
                z-index: 9999; 
                padding: 10px;
                border-radius: 10px;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.3);">
        <h3 style="margin: 0; color: #d4af37;">&#127942; Tour TSP Concorde (Optimal)</h3>
        <p style="margin: 5px 0; font-size: 14px;">
            <b>Villes:</b> {len(tour_order)}<br>
            <b>Distance totale:</b> {total_distance_km:,.2f} km
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add tour path
    path_coords = [(lat, lon) for lat, lon in tour_coords]
    
    folium.PolyLine(
        path_coords,
        weight=2,
        color='#d4af37',
        opacity=0.8,
        tooltip=f"Distance totale: {total_distance_km:,.2f} km"
    ).add_to(m)
    
    # Start marker (green)
    folium.Marker(
        tour_coords[0],
        popup=f"<b>DEPART</b><br>Ville: {tour_ids[0]}<br>Position: 1",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    
    # Add marker cluster
    marker_cluster = plugins.MarkerCluster(name='Villes').add_to(m)
    
    for i, (coord, ville_id) in enumerate(zip(tour_coords[:-1], tour_ids[:-1])):
        folium.CircleMarker(
            location=coord,
            radius=4,
            color='#d4af37',
            fill=True,
            fill_color='#ffd700',
            fill_opacity=0.7,
            popup=f"Ville: {ville_id}<br>Position: {i+1}"
        ).add_to(marker_cluster)
    
    folium.LayerControl().add_to(m)
    plugins.Fullscreen().add_to(m)
    
    m.save(output_path)
    print(f"\nCarte generee: {os.path.abspath(output_path)}")
    
    return total_distance_km


if __name__ == '__main__':
    print("Concorde Tour Visualization")
    print("(c) 2026 iM@Des")
