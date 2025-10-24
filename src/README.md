# Overview

This is the backend API for Rescue Box, powered by FastAPI and postgreSQL backed SQLModel.

# Installing PostreSQL and pgvector

We use SQLModel to connect to a locally running PostgreSQL database instance. We need
to ensure there is a user named `rescue_box` running on the database.

## Install PG and pgvector

```
# install PG
brew install postgresql@17

# Install pgvector (if this does not work, so the alternative instructions below):
brew install pgvector

# Start PG (per output of brew install command above)
brew services start postgresql@17
```

## Connect to the database and add a rescue_box user and database:

```
# Connect to the default postgres database (using your local username):
psql -U [local username] -d postgres

; Run these database commands from psql:
CREATE DATABASE rescue_box;
CREATE USER rescue_box;
GRANT ALL PRIVILEGES ON DATABASE rescue_box TO rescue_box;
GRANT ALL ON SCHEMA public TO rescue_box;
CREATE EXTENSION vector;
```


## pgvector alternative instructions

### install PG vector from source (if homebrew did not work)
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
inside psql
CREATE EXTENSION vector;
\dx  -- check installed extensions, vector should be listed
