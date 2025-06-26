from flask import Flask, request, redirect, session, jsonify
import requests
import os

app = Flask(__name__)
app.secret_key = "secreto_super_seguro"

# Configuración de GitHub OAuth
GITHUB_CLIENT_ID = "Ov23liacoljiSrUe6kfS"
GITHUB_CLIENT_SECRET = "7c393bf1a7658a1ec43915fdd7fb7be304d4a3fe"
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com/user"

@app.route("/")
def home():
    """Página de inicio con botón para iniciar sesión en GitHub."""
    return '<a href="/login">🔑 Iniciar sesion con GitHub</a>'

@app.route("/login")
def login():
    """Redirige a GitHub para iniciar sesión."""
    return redirect(f"{GITHUB_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}&scope=repo")

@app.route("/callback")
def callback():
    """Recibe el código de GitHub y obtiene el token de acceso."""
    code = request.args.get("code")
    
    if not code:
        return "ERROR: No se recibió código de autorización", 400

    # Intercambiar el código por un token de acceso
    token_response = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code}
    )
    
    token_data = token_response.json()
    session["github_token"] = token_data.get("access_token")

    return redirect("/perfil")

@app.route("/perfil")
def perfil():
    """Muestra información del usuario autenticado."""
    token = session.get("github_token")

    if not token:
        return redirect("/login")

    user_response = requests.get(GITHUB_API_URL, headers={"Authorization": f"token {token}"})
    user_data = user_response.json()

    return jsonify(user_data)

@app.route("/commits")
def obtener_commits():
    """Obtiene los commits recientes del usuario autenticado."""
    token = session.get("github_token")

    if not token:
        return redirect("/login")

    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(f"https://api.github.com/user/repos", headers=headers)

    if response.status_code != 200:
        return f"ERROR al obtener repositorios: {response.status_code}", 400

    repos = response.json()
    commits_data = []

    for repo in repos:
        repo_name = repo["full_name"]
        commits_response = requests.get(f"https://api.github.com/repos/{repo_name}/commits", headers=headers)

        if commits_response.status_code == 200:
            commits = commits_response.json()
            for commit in commits:
                commits_data.append({
                    "repositorio": repo_name,
                    "autor": commit["commit"]["author"]["name"],
                    "mensaje": commit["commit"]["message"],
                    "fecha": commit["commit"]["author"]["date"],
                    "url": commit["html_url"]
                })

    return jsonify(commits_data)


if __name__ == "__main__":
    app.run(debug=True)

