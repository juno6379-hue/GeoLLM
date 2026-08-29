import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import text
from data.database import get_enc_db
from shared.observability.logger import get_logger

logger = get_logger("scripts.create_db_indexes")

def create_indexes():
    db_gen = get_enc_db()
    db = next(db_gen)
    
    if not db:
        logger.error("Failed to connect to GBENC DB.")
        return
        
    indexes = [
        """
        CREATE INDEX IF NOT EXISTS idx_codeinformation_type_code
        ON codeinformation (type, code);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_codeinformation_name
        ON codeinformation (name);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_rulefunctions_feature_name
        ON rulefunctions (featurename);
        """
        # Note: idx_feature_geom and idx_feature_nftc on enc_feature
        # are created if applicable. We will assume the table is enc_feature
    ]
    
    # Try creating index on feature as well
    feature_indexes = [
        """
        CREATE INDEX IF NOT EXISTS idx_feature_geom
        ON feature USING GIST (geom);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_feature_nftc
        ON feature (nftc);
        """
    ]
    
    for stmt in indexes:
        try:
            db.execute(text(stmt))
            db.commit()
            logger.info(f"Executed: {stmt.strip()}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to execute: {stmt.strip()}", error=str(e))
            
    for stmt in feature_indexes:
        try:
            db.execute(text(stmt))
            db.commit()
            logger.info(f"Executed: {stmt.strip()}")
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to execute (table might not exist yet): {stmt.strip()}", error=str(e))
            
    logger.info("Index creation finished.")

if __name__ == "__main__":
    create_indexes()
