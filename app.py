from flask import Flask, request, jsonify, session, redirect, send_from_directory
import sqlite3
import os
import hashlib

app = Flask(__name__)

# Chave usada para proteger a sessão do usuário
app.secret_key = "silver-mind-chave-teste-2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "silvermind.db")


# =========================================
# BANCO DE DADOS
# =========================================

def conectar_banco():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_banco():
    conexao = conectar_banco()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


# =========================================
# CRIPTOGRAFIA DA SENHA
# =========================================

def criar_hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


# =========================================
# PÁGINAS
# =========================================

@app.route("/")
def inicio():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/pages/<path:arquivo>")
def paginas(arquivo):
    return send_from_directory(
        os.path.join(BASE_DIR, "pages"),
        arquivo
    )


@app.route("/assets/<path:arquivo>")
def assets(arquivo):
    return send_from_directory(
        os.path.join(BASE_DIR, "assets"),
        arquivo
    )


@app.route("/css/<path:arquivo>")
def css(arquivo):
    return send_from_directory(
        os.path.join(BASE_DIR, "css"),
        arquivo
    )


@app.route("/js/<path:arquivo>")
def js(arquivo):
    return send_from_directory(
        os.path.join(BASE_DIR, "js"),
        arquivo
    )


# =========================================
# CADASTRO
# =========================================

@app.route("/api/cadastro", methods=["POST"])
def cadastro():

    dados = request.get_json()

    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({
            "sucesso": False,
            "mensagem": "Preencha todos os campos."
        }), 400

    if len(senha) < 6:
        return jsonify({
            "sucesso": False,
            "mensagem": "A senha precisa ter pelo menos 6 caracteres."
        }), 400

    conexao = conectar_banco()

    usuario_existente = conexao.execute(
        "SELECT id FROM usuarios WHERE email = ?",
        (email,)
    ).fetchone()

    if usuario_existente:
        conexao.close()

        return jsonify({
            "sucesso": False,
            "mensagem": "Este e-mail já possui uma conta."
        }), 409

    senha_hash = criar_hash_senha(senha)

    conexao.execute(
        """
        INSERT INTO usuarios (nome, email, senha)
        VALUES (?, ?, ?)
        """,
        (nome, email, senha_hash)
    )

    conexao.commit()
    conexao.close()

    return jsonify({
        "sucesso": True,
        "mensagem": "Conta criada com sucesso!"
    })


# =========================================
# LOGIN
# =========================================

@app.route("/api/login", methods=["POST"])
def login():

    dados = request.get_json()

    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")

    if not email or not senha:
        return jsonify({
            "sucesso": False,
            "mensagem": "Digite seu e-mail e sua senha."
        }), 400

    senha_hash = criar_hash_senha(senha)

    conexao = conectar_banco()

    usuario = conexao.execute(
        """
        SELECT id, nome, email
        FROM usuarios
        WHERE email = ? AND senha = ?
        """,
        (email, senha_hash)
    ).fetchone()

    conexao.close()

    if not usuario:
        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail ou senha incorretos."
        }), 401

    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session["usuario_email"] = usuario["email"]

    return jsonify({
        "sucesso": True,
        "mensagem": "Login realizado com sucesso!",
        "nome": usuario["nome"]
    })


# =========================================
# USUÁRIO LOGADO
# =========================================

@app.route("/api/usuario")
def usuario_logado():

    if "usuario_id" not in session:
        return jsonify({
            "logado": False
        })

    return jsonify({
        "logado": True,
        "id": session["usuario_id"],
        "nome": session["usuario_nome"],
        "email": session["usuario_email"]
    })


# =========================================
# LOGOUT
# =========================================

@app.route("/api/logout")
def logout():

    session.clear()

    return jsonify({
        "sucesso": True
    })


# =========================================
# PROTEÇÃO DA ÁREA DO ALUNO
# =========================================

@app.route("/aluno")
def area_aluno():

    if "usuario_id" not in session:
        return redirect("/pages/login.html")

    return send_from_directory(
        os.path.join(BASE_DIR, "pages"),
        "area-aluno.html"
    )


# =========================================
# INICIAR SISTEMA
# =========================================

if __name__ == "__main__":

    criar_banco()

    print("")
    print("======================================")
    print(" SILVER MIND")
    print(" Sistema iniciado com sucesso")
    print("======================================")
    print("")
    print("Acesse:")
    print("http://127.0.0.1:5000")
    print("")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )