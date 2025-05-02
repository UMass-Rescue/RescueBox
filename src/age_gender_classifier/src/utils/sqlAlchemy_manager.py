from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import logging


Base = declarative_base()


class LabeledAges(Base):
    __tablename__ = "age_gender_labeled"
    id = Column(Integer, primary_key=True, autoincrement=True)
    age = Column(Integer, nullable=True)
    ethnicity = Column(Integer, nullable=True)
    gender = Column(Boolean, nullable=True)
    img_name = Column(String, nullable=True)
    pixels = Column(String, nullable=True)


class ModelOutput(Base):
    __tablename__ = "model_output"
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String, nullable=False)
    scores = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())


defined_tables = {"age_gender_labeled": LabeledAges, "model_output": ModelOutput}


class DBManager:
    def __init__(self, db_url: str, table_name: str) -> None:
        """Initialize the database connection.

        Args:
            db_url (str): The database connection URL.
            table_name (str): The table name to operate on.
        """
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

        if table_name not in defined_tables:
            raise ValueError(f"Table '{table_name}' is not recognized.")
        self.table = defined_tables[table_name]

    def create_table_if_not_exists(self) -> None:
        """Create the users table if it does not exist."""
        Base.metadata.create_all(self.engine)

    def insert_record(self, **kwargs) -> None:
        """Insert a new record into the specified table.

        Args:
            kwargs: Column values for the table.
        """
        session = self.Session()
        try:
            new_rec = self.table(**kwargs)
            session.add(new_rec)
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error inserting record: {e}")
        finally:
            session.close()

    def update_record(self, record_id: int, **kwargs) -> None:
        """Update an existing record in the specified table.

        Args:
            record_id (int): The ID of the record to update.
            kwargs: Fields to update with new values.
        """
        session = self.Session()
        try:
            rec = session.query(self.table).filter_by(id=record_id).first()
            if rec:
                for key, value in kwargs.items():
                    if hasattr(rec, key):
                        setattr(rec, key, value)
                session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating record: {e}")
        finally:
            session.close()

    def delete_user(self, record_id: int) -> None:
        """Delete a record from the specified table by ID.

        Args:
            record_id (int): The ID of the record to delete.
        """
        session = self.Session()
        try:
            rec = session.query(self.table).filter_by(id=record_id).first()
            if rec:
                session.delete(rec)
                session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting record: {e}")
        finally:
            session.close()

    def truncate_table(self) -> None:
        """Truncate the specified table."""
        session = self.Session()
        try:
            session.execute(text(f"DELETE FROM {self.table.__tablename__}"))
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error truncating table {self.table.__tablename__}: {e}")
        finally:
            session.close()

    def drop_table(self, table: str) -> None:
        """Drop specified table."""
        session = self.Session()
        try:
            session.execute(text(f"DROP TABLE IF EXISTS {table}"))
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error dropping table {table}: {e}")
        finally:
            session.close()
