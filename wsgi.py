import os

os.chdir(os.path.join(os.path.abspath("."), "backend"))

from zero_ci import app_with_session
