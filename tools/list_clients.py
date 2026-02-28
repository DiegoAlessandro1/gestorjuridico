from app import create_app
from app.config import get_db

app = create_app()
with app.app_context():
    db = get_db()
    clientes = list(db['clientes'].find())
    print('Total clientes:', len(clientes))
    for c in clientes:
        print(c.get('nome'), '|', c.get('cpf_cnpj'))
