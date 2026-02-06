# -*- coding: utf-8 -*-
"""
TSP Converter for Concorde - Gibraltar Projection
Distance: Euclidean (same projection as TSP file)
(c) 2026 iM@Des
"""

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, Tuple
import os, re

EARTH_RADIUS_M = 6371008.8
GIBRALTAR_LAT = 36.57  # Gibraltar precis

def gps_to_meters_gibraltar(lat, lon, ref_lon=0.0):
    x = EARTH_RADIUS_M * radians(lon - ref_lon) * cos(radians(GIBRALTAR_LAT))
    y = EARTH_RADIUS_M * radians(lat - GIBRALTAR_LAT)
    return x, y

def euclidean_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1_rad, lat2_rad = radians(lat1), radians(lat2)
    a = sin(radians(lat2-lat1)/2)**2 + cos(lat1_rad)*cos(lat2_rad)*sin(radians(lon2-lon1)/2)**2
    return EARTH_RADIUS_M * 2 * atan2(sqrt(a), sqrt(1-a))

def detect_columns(df):
    cols = {c.lower(): c for c in df.columns}
    lat = lon = id_col = None
    for p in ['latitude','lat','y','y-coordinate']: 
        if p in cols: lat = cols[p]; break
    for p in ['longitude','lon','x','x-coordinate']: 
        if p in cols: lon = cols[p]; break
    for p in ['id','commune','name']: 
        if p in cols: id_col = cols[p]; break
    if not id_col and df.columns.size: id_col = df.columns[0]
    return id_col, lat, lon

class ExcelToTSPConverter:
    def __init__(self, path, id_col='commune', lat_col='latitude', lon_col='longitude'):
        self.input_path, self.id_col, self.lat_col, self.lon_col = path, id_col, lat_col, lon_col
        self.df, self.ref_lat, self.ref_lon, self.projected_coords = None, GIBRALTAR_LAT, None, None
        self._load()
    
    def _load(self):
        ext = os.path.splitext(self.input_path)[1].lower()
        self.df = pd.read_excel(self.input_path) if ext in ['.xlsx','.xls'] else pd.read_csv(self.input_path)
        print(f"[INFO] Charge {len(self.df)} points")
    
    def project_coordinates(self):
        lats, lons = self.df[self.lat_col].values, self.df[self.lon_col].values
        self.ref_lon = np.mean(lons)
        self.projected_coords = np.array([gps_to_meters_gibraltar(lats[i], lons[i], self.ref_lon) for i in range(len(self.df))])
        print(f"[INFO] Projection Gibraltar (ref_lat={GIBRALTAR_LAT}, ref_lon={self.ref_lon:.6f})")
        return self.projected_coords
    
    def generate_tsp_file(self, path, name=None):
        if self.projected_coords is None: self.project_coordinates()
        name = name or os.path.splitext(os.path.basename(path))[0]
        with open(path, 'w') as f:
            f.write(f"NAME : {name}\nCOMMENT : Gibraltar (lat={GIBRALTAR_LAT}, lon={self.ref_lon:.6f})\nTYPE : TSP\nDIMENSION : {len(self.df)}\nEDGE_WEIGHT_TYPE : EUC_2D\nNODE_COORD_SECTION\n")
            for i, (x,y) in enumerate(self.projected_coords): f.write(f"{i+1} {x:.6f} {y:.6f}\n")
            f.write("EOF\n")
        print(f"[INFO] TSP genere: {path}")
        return path

class ConcordeSolConverter:
    def __init__(self, sol_path, data_path, id_col='commune', lat_col='latitude', lon_col='longitude'):
        self.sol_path, self.data_path = sol_path, data_path
        self.id_col, self.lat_col, self.lon_col = id_col, lat_col, lon_col
        self.tour_order, self.original_df, self.projected_coords, self.ref_lon = [], None, None, None
        self._load()
    
    def _load(self):
        ext = os.path.splitext(self.data_path)[1].lower()
        self.original_df = pd.read_excel(self.data_path) if ext in ['.xlsx','.xls'] else pd.read_csv(self.data_path)
        lats, lons = self.original_df[self.lat_col].values, self.original_df[self.lon_col].values
        self.ref_lon = np.mean(lons)
        self.projected_coords = np.array([gps_to_meters_gibraltar(lats[i], lons[i], self.ref_lon) for i in range(len(self.original_df))])
        with open(self.sol_path) as f: lines = f.readlines()
        for line in lines[1:]:
            for p in line.split():
                try: self.tour_order.append(int(p))
                except: pass
        print(f"[INFO] Solution: {len(self.tour_order)} villes")
    
    def calculate_total_distance(self, ref_lat=GIBRALTAR_LAT, ref_lon=None):
        """Distance Euclidienne (meme projection que TSP)"""
        total = sum(euclidean_distance(*self.projected_coords[self.tour_order[i]], *self.projected_coords[self.tour_order[(i+1)%len(self.tour_order)]]) for i in range(len(self.tour_order)))
        return total / 1000.0
    
    def calculate_haversine_distance(self):
        """Distance Haversine (reference GPS)"""
        lats, lons = self.original_df[self.lat_col].values, self.original_df[self.lon_col].values
        total = sum(haversine_distance(lats[self.tour_order[i]], lons[self.tour_order[i]], lats[self.tour_order[(i+1)%len(self.tour_order)]], lons[self.tour_order[(i+1)%len(self.tour_order)]]) for i in range(len(self.tour_order)))
        return total / 1000.0
    
    def generate_output(self, path, fmt='xlsx'):
        df = self.original_df.copy()
        df['ordre_visite'] = 0
        for i, node in enumerate(self.tour_order, 1): df.loc[node, 'ordre_visite'] = i
        df = df.sort_values('ordre_visite')
        df.to_excel(path, index=False) if fmt != 'csv' else df.to_csv(path, index=False)
        print(f"[INFO] Resultat: {path}")
        return path

if __name__ == '__main__':
    print("TSP Converter - Gibraltar Projection")

