from flask import Flask
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        # Registrar Blueprints
        from app.routes.webhook import webhook_bp
        from app.routes.send_message import send_message_bp

        app.register_blueprint(webhook_bp)
        app.register_blueprint(send_message_bp)

    return app
