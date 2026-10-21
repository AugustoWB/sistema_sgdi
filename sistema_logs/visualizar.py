from flask import Flask, render_template, request

try:
    from registro import TIPOS, listar_logs
except ImportError:
    from sistema_logs.registro import TIPOS, listar_logs


app = Flask(__name__)


@app.route('/')
def index():
    tipo = request.args.get('tipo', '').strip()
    if tipo not in TIPOS:
        tipo = ''

    logs = listar_logs(tipo or None)

    return render_template(
        'index.html',
        logs=logs,
        tipos=TIPOS,
        tipo=tipo,
    )


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
