from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    titulo = "Inicio"
    return render_template("index.html", titulo=titulo)

@app.route("/about")
def about():
    titulo = "Acerca de"
    return render_template("about.html", titulo=titulo)

@app.route("/usuario/<nombre>")
def usuario(nombre):
    # Ejemplo de pasar datos dinámicos
    return render_template("index.html", titulo="Perfil", nombre=nombre)

if __name__ == "__main__":
    app.run(debug=True)
