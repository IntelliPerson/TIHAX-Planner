from flask import Flask, request, jsonify
import time

flaskapp = Flask(__name__)

def create_app_object(app_obj):
    global app
    app = app_obj

@flaskapp.route("/status", methods=["GET"])
def status():
    vehicle = app.vehicle
    if app.hedefvar==1:
        drone_lat = app.vehicle.location.global_frame.lat 
        drone_lon = app.vehicle.location.global_frame.lon 
        current_location = app.vehicle.location.global_relative_frame
        uzaklik = app.get_distance_metres(current_location,app.target_location)
    if not vehicle:
        return jsonify({"status": "Cihaz Bağlı Değil"})
    return jsonify({
        "Yükseklik": vehicle.location.global_relative_frame.alt,
        "Şarj seviyesi": vehicle.battery.level,
        "uçuş Modu": str(vehicle.mode),
        "Motor durumu": vehicle.armed,
        "hedef var": app.hedefvar,
        "Hedefe Uzaklık" : uzaklik
    })

@flaskapp.route('/execute', methods=['POST'])
def execute_command():
    data = request.get_json()

    # Komutları sırasıyla işle
    
    func_name = data.get("function")
    args = data.get("args", [])

    # Fonksiyon ismi ve parametreleri alıp çağırma
    if func_name == "takeoff":
        app.takeoff_drone(1,*args)
        print(*args)
    elif func_name == "wait":
        #wait(*args)
        time.sleep(*args)
    elif func_name == "RTL":
        app.RTL(0)
    elif func_name == "forward":
        print("a")
    elif func_name == "back":
        print("a")
    elif func_name == "right":
        print("a")
    elif func_name == "left":
        print("a")
    elif func_name == "backtolastwp":   
        print("a")
    elif func_name == "gotoaddress":
        app.flight_to(*args)
    elif func_name == "follow":
        app.changeMode("Follow")
    elif func_name == "lidarmapping":
        print("a")
    elif func_name == "mapping":
        app.mapping(*args)
    elif func_name == "land":
        app.land_drone()
    else:
        print(f"[FAKE SERVER] Bilinmeyen komut: {func_name}")
        return jsonify({"status": "error", "message": f"Bilinmeyen komut: {func_name}"}), 400

    print(f"📥 Komut alındı: {func_name}({', '.join(map(str, args))})")

    # Komutu simüle et (örneğin 2 saniye bekleyelim)
    #time.sleep(2)

    print(f"✅ Komut tamamlandı: {func_name}")
    return jsonify({"status": "done"})