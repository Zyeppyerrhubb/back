from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import uuid
import os

app = Flask(__name__)
CORS(app)

# Helper: Load & Save JSON
def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# === Routes ===
@app.route("/")
def home():
    return "✅ Backend ZYEN STORE aktif!"

@app.route("/produk", methods=["GET"])
def get_produk():
    return jsonify(load_json("produk.json"))

# ✅ === CHECKOUT (sinkron ke frontend) ===
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()

    required = ["nama", "harga", "jumlah", "nickname", "nowa", "metode", "id"]
    if not all(k in data for k in required):
        return jsonify({"message": "Data tidak lengkap"}), 400

    pesanan = load_json("pesanan.json")
    transaksi_id = str(uuid.uuid4())

    new_order = {
        "id": transaksi_id,
        "nama_produk": data["nama"],
        "harga": data["harga"],
        "jumlah": data["jumlah"],
        "nickname": data["nickname"],
        "nowa": data["nowa"],
        "metode": data["metode"],
        "status": "pending"
    }

    pesanan.append(new_order)
    save_json("pesanan.json", pesanan)

    return jsonify({"status": "pending", "transaksi_id": transaksi_id})

# ✅ === CEK STATUS (sinkron ke polling frontend) ===
@app.route("/status/<id>", methods=["GET"])
def status(id):
    pesanan = load_json("pesanan.json")
    for p in pesanan:
        if p["id"] == id:
            return jsonify({
                "status": p["status"],
                "produk": p["nama_produk"],
                "jumlah": p["jumlah"],
                "total": p["harga"] * p["jumlah"],
                "nickname": p["nickname"],
                "metode": p["metode"]
            })
    return jsonify({"status": "not found"}), 404

# === ADMIN: semua pesanan
@app.route("/pesanan", methods=["GET"])
def pesanan_all():
    return jsonify(load_json("pesanan.json"))

# === ADMIN: ubah status
@app.route("/ubah_status/<id>", methods=["POST"])
def ubah_status(id):
    data = request.json
    pesanan = load_json("pesanan.json")
    for p in pesanan:
        if p["id"] == id:
            p["status"] = data.get("status", "pending")
            save_json("pesanan.json", pesanan)
            return jsonify({"message": f"Status pesanan diubah ke {p['status']}"})
    return jsonify({"message": "Pesanan tidak ditemukan"}), 404

# === ADMIN PAGE (jika perlu)
@app.route("/admin", methods=["GET"])
def admin():
    return send_file("admin.html")

# === Start Server ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
