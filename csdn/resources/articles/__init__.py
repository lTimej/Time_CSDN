from flask import Blueprint
from flask_restful import Api

article_bp = Blueprint('article',__name__)

article_api = Api(article_bp,catch_all_404s=True)
