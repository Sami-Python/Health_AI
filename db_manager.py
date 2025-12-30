
import duckdb
import json
from datetime import datetime

DB_FILE = "health_ai.db"

def init_db():
    """Initializes the database table if it doesn't exist."""
    con = duckdb.connect(DB_FILE)
    con.execute("""
        CREATE SEQUENCE IF NOT EXISTS plan_id_seq;
        CREATE TABLE IF NOT EXISTS training_plans (
            id INTEGER PRIMARY KEY DEFAULT nextval('plan_id_seq'),
            timestamp TIMESTAMP,
            predicted_charge INTEGER,
            advice_text TEXT,
            context_json TEXT,
            status TEXT DEFAULT 'PENDING'
        );
    """)
    
    # Simple migration for existing tables without status
    try:
        con.execute("ALTER TABLE training_plans ADD COLUMN status TEXT DEFAULT 'PENDING'")
    except:
        pass # Column likely exists
        
    con.close()

def save_plan(context, advice_text):
    """Saves a generated training plan."""
    con = duckdb.connect(DB_FILE)
    
    # Extract relevant fields for easier querying, but store full context as JSON
    predicted_charge = context.get('predicted_charge', 0)
    context_str = json.dumps(context)
    timestamp = datetime.now()
    
    con.execute("""
        INSERT INTO training_plans (timestamp, predicted_charge, advice_text, context_json, status)
        VALUES (?, ?, ?, ?, 'PENDING')
    """, (timestamp, predicted_charge, advice_text, context_str))
    
    con.close()
    print("Plan saved to DuckDB.")

def update_plan_status(plan_id, new_status):
    """Updates the status of a plan (DONE, SKIPPED)."""
    con = duckdb.connect(DB_FILE)
    con.execute("UPDATE training_plans SET status = ? WHERE id = ?", (new_status, plan_id))
    con.close()

def get_latest_plan():
    """Retrieves the most recent training plan."""
    con = duckdb.connect(DB_FILE)
    
    try:
        result = con.execute("""
            SELECT advice_text, timestamp, id, status FROM training_plans 
            ORDER BY timestamp DESC 
            LIMIT 1
        """).fetchone()
    except duckdb.CatalogException:
        return None
    finally:
        con.close()
        
    if result:
        return {
            "content": result[0], 
            "date": str(result[1]),
            "id": result[2],
            "status": result[3]
        }
    return None

def get_recent_plans(limit=10):
    """Retrieves recent plans for history view."""
    con = duckdb.connect(DB_FILE)
    try:
        results = con.execute(f"""
            SELECT id, timestamp, predicted_charge, advice_text, status 
            FROM training_plans 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        """).fetchall()
        
        plans = []
        for r in results:
            plans.append({
                "id": r[0],
                "timestamp": r[1],
                "charge": r[2],
                "advice": r[3],
                "status": r[4]
            })
        return plans
    except:
        return []
    finally:
        con.close()
