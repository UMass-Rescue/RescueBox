"""Exception types commonly caught in SQLite and persistence layers."""

import sqlite3

from frontend.utils.exceptions import UI_RENDER_ERRORS

DB_ERRORS = (*UI_RENDER_ERRORS, sqlite3.Error)
