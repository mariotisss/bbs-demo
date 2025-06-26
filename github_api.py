from flask import Flask, request, redirect, session, jsonify, render_template_string
import requests
import pandas as pd

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
    return '<a href="/login">🔑 Iniciar sesión con GitHub</a>'

@app.route("/login")
def login():
    return redirect(f"{GITHUB_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}&scope=repo")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "ERROR: No se recibió código de autorización", 400

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
    token = session.get("github_token")
    if not token:
        return redirect("/login")

    user_response = requests.get(GITHUB_API_URL, headers={"Authorization": f"token {token}"})
    user_data = user_response.json()
    return jsonify(user_data)

@app.route("/commits")
def obtener_commits():
    token = session.get("github_token")
    if not token:
        return redirect("/login")

    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get("https://api.github.com/user/repos", headers=headers)
    if response.status_code != 200:
        return f"ERROR al obtener repositorios: {response.status_code}", 400

    repos = response.json()
    commit_counts = {}

    for repo in repos:
        repo_name = repo["full_name"]
        commits_response = requests.get(f"https://api.github.com/repos/{repo_name}/commits", headers=headers)

        if commits_response.status_code == 200:
            commits = commits_response.json()
            commit_counts[repo_name] = len(commits)

    df = pd.DataFrame(list(commit_counts.items()), columns=["Repositorio", "Total Commits"])
    df = df.sort_values(by="Total Commits", ascending=False)

    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resumen de Commits</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { width: 50%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid black; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h2>Resumen de Commits</h2>
        <table>
            <tr>
                <th>Repositorio</th>
                <th>Total Commits</th>
            </tr>
            {% for repo, commits in data %}
            <tr>
                <td>{{ repo }}</td>
                <td>{{ commits }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, data=df.values.tolist())


if __name__ == "__main__":
    app.run(debug=True)
