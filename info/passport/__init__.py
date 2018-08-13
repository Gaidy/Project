from flask import Blueprint

passport_bule = Blueprint("passport",__name__,url_prefix="/passport")

from . import view