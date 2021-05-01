# from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb()
from .db_routing.routing_sqlalchemy import RoutingSQLAlchemy

db = RoutingSQLAlchemy()
