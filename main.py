from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import uuid

app = Flask(__name__)
CORS(app)

# ===== Helper Function =====
def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ===== ROUTES =====

@app.route("/")
def home():
    return "✅ Backend ZYEN STORE aktif!"

# API: Ambil semua produk
@app.route("/api/produk", methods=["GET"])
def get_produk():
    produk = load_json("produk.json")
    return jsonify(produk)

# Alias /produk untuk frontend lama
@app.route("/produk", methods=["GET"])
def produk_plain():
    produk = load_json("produk.json")
    return jsonify(produk)

# API: Checkout produk
@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.json
    pesanan = load_json("pesanan.json")

    id_transaksi = str(uuid.uuid4())
    data["id"] = id_transaksi
    data["status"] = "pending"
    pesanan.append(data)
    save_json("pesanan.json", pesanan)
    return jsonify({"message": "Checkout berhasil", "id": id_transaksi})

# API: Cek status pesanan
@app.route("/api/status/<id>", methods=["GET"])
def get_status(id):
    pesanan = load_json("pesanan.json")
    for p in pesanan:
        if p["id"] == id:
            return jsonify({"status": p["status"]})
    return jsonify({"status": "not found"}), 404

# API: List semua pesanan
@app.route("/api/pesanan", methods=["GET"])
def get_pesanan():
    return jsonify(load_json("pesanan.json"))

# API: Ubah status pesanan
@app.route("/api/ubah_status/<id>", methods=["POST"])
def ubah_status(id):
    data = request.json
    status_baru = data.get("status")
    pesanan = load_json("pesanan.json")
    for p in pesanan:
        if p["id"] == id:
            p["status"] = status_baru
            save_json("pesanan.json", pesanan)
            return jsonify({"message": "Status diubah"})
    return jsonify({"message": "Pesanan tidak ditemukan"}), 404

# Halaman admin (pastikan admin.html ada di folder yang sama)
@app.route("/admin", methods=["GET"])
def admin_page():
    return send_file("admin.html")

# ====== RUN APP ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
