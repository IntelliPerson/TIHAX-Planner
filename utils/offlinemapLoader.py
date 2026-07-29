"""import tkintermapview
import os
top_left_position = (40.791811, 30.363097)  # Sol üst köşe
bottom_right_position = (40.753075, 30.427366)  # Sağ alt köşe

zoom_min = 19   # Sakarya'nın tamamı için mantıklı başlangıç zoom
zoom_max = 20  # Daha fazla detay için maksimum zoom

# script dizini ve veritabanı yolu
script_directory = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(script_directory, "offline_tiles.db")

# OfflineLoader oluşturuluyor
loader = tkintermapview.OfflineLoader(
    path=database_path,
    tile_server="https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga"  # açık kaynak tile server
)

# Karoları indir ve veritabanına kaydet
loader.save_offline_tiles(top_left_position, bottom_right_position, zoom_min, zoom_max)

# Yüklenen bölümleri yazdır
loader.print_loaded_sections()"""

import tkinter as tk
from tkintermapview import TkinterMapView

# Ana pencere
root = tk.Tk()
root.geometry("800x600")
root.title("Sakarya Offline Harita")

# Harita widget'ı
map_widget = TkinterMapView(root,
                            width=800,
                            height=600,
                            corner_radius=0,
                            use_database_only=True,
                            database_path="./offline_tiles.db")

map_widget.pack(fill="both", expand=True)

# OFFLINE kullanım ayarları
map_widget.set_tile_server(
    "https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga",  # Aynı tile server  # İndirdiğin veritabanının yolu
      # Sadece offline kullan
)

# Başlangıç konumu (Sakarya merkezi)
map_widget.set_position(40.7769240, 30.3914130)
map_widget.set_zoom(15)

root.mainloop()