import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager

from db import db
from blocklist import BLOCKLIST

from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint


def create_app(db_url=None):
    app = Flask(__name__)

    # --- Flask Configuration ---
    # Propagate exceptions to ensure errors are handled and returned as JSON
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"

    # --- OpenAPI / Swagger UI Setup ---
    # Configuration for automatic API documentation generation
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # --- OpenAPI / Swagger UI Setup ---
    # Configuration for automatic API documentation generation
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    
    api = Api(app)

    # --- JWT Authentication Setup ---
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    jwt = JWTManager(app)


    # Check if a token exists in the blocklist (used for logging out)
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blacklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST
    

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked", "error": "token_revoked"}
                ), 401
            )
    

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh",
                    "error": "fresh_token_required"
                }
            ),
            401
        )


    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"message": "the token has expired", "error":"token_expired"}
                ), 401
            )
        
    
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
                ), 401
            )
    
    
    # Custom response when no token is provided in the headers
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                { "description": "Requestdoes not contain an access token.","error": "authorization_required"}
                ), 401
            )

    # # Configure what should be stored in the JWT's identity field
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """
        Convert a user object to a string identity for the JWT.
        Returns the user's ID or the object itself if no ID attribute exists.
        """
        return str(user.id) if hasattr(user, 'id') else str(user)


    # --- Database Initialization ---
    # Create database tables if they don't already exist
    with app.app_context():
        db.create_all()

    # --- Blueprint Registration ---
    # Register different API modules to the main application
    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app








