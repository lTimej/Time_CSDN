from flask import Blueprint
from flask_restful import Api
from utils.output import output_json

bp_search = Blueprint("search",__name__)

search_api = Api(bp_search,catch_all_404s=True)
search_api.representation('application/json')(output_json)
