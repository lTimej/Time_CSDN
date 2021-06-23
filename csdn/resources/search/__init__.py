from flask import Blueprint
from flask_restful import Api
from utils.output import output_json
from . import searchs,history

bp_search = Blueprint("search",__name__)

search_api = Api(bp_search,catch_all_404s=True)
search_api.representation('application/json')(output_json)

search_api.add_resource(searchs.AllSearchView,"/v1/user/search",endpoint="search")
search_api.add_resource(history.UserHistorySearchRecord,"/v1/search/history",endpoint="sHistory")