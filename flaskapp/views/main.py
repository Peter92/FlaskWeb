from flask import Blueprint

from ..database import *


app = Blueprint(__name__, __name__, template_folder='templates')
