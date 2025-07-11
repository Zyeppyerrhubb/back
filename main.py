from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import uuid

app = Flask(__name__)
CORS(app)

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/produk", methods=["GET"])
def get_produk():
    produk = load_json("produk.json")
    return jsonify(produk)

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.json
    pesanan = load_json("pesanan.json")

    id_transaksi = str(uuid.uuid4())
    data["id"] = id_transaksi
    data["status"] = "pending"
    pesanan.append(data)
    save_json("pesanan.json", pesanan)
    return jsonify({"message": "Checkout berhasil", "id": id_transaksi})

@app.route("/status/<id>", methods=["GET"])
def get_status(id):
    pesanan = load_json("pesanan.json")
    for p in pesanan:
        if p["id"] == id:
            return jsonify({"status": p["status"]})
    return jsonify({"status": "not found"}), 404

@app.route("/pesanan", methods=["GET"])
def get_pesanan():
    return jsonify(load_json("pesanan.json"))

@app.route("/ubah_status/<id>", methods=["POST"])
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

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user_db = load_json("user.json")
    for u in user_db:
        if u["username"] == data["username"] and u["password"] == data["password"]:
            return jsonify({"message": "Login sukses", "role": u["role"]})
    return jsonify({"message": "Login gagal"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
