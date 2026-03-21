import sys
import traceback
from flask import Flask, jsonify


def _criar_app_degradada(erro):
	app_degradada = Flask(__name__)

	@app_degradada.get('/')
	def degraded_root():
		return jsonify({
			'success': False,
			'message': 'Aplicacao inicializada em modo degradado',
			'error': str(erro)
		}), 500

	@app_degradada.get('/healthz')
	def degraded_health():
		return jsonify({'status': 'degraded'}), 200

	return app_degradada


try:
	from backend.app import create_app
	app = create_app()

	@app.get('/healthz')
	def healthz():
		return jsonify({'status': 'ok'}), 200

except Exception as exc:
	print(f"[ERRO] Falha ao inicializar aplicacao Flask: {exc}", file=sys.stderr)
	traceback.print_exc()
	app = _criar_app_degradada(exc)
