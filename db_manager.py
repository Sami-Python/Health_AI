
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
        CREATE SEQUENCE IF NOT EXISTS analysis_id_seq;
        CREATE TABLE IF NOT EXISTS trend_analysis (
            id INTEGER PRIMARY KEY DEFAULT nextval('analysis_id_seq'),
            timestamp TIMESTAMP,
            content TEXT,
            context_json TEXT
        );
        CREATE SEQUENCE IF NOT EXISTS daily_id_seq;
        CREATE TABLE IF NOT EXISTS daily_workouts (
            id INTEGER PRIMARY KEY DEFAULT nextval('daily_id_seq'),
            plan_id INTEGER,
            day_offset INTEGER,
            content TEXT,
            status TEXT DEFAULT 'PENDING'
        );
    """)
    
    # Simple migration for existing tables without status
    try:
        con.execute("ALTER TABLE training_plans ADD COLUMN status TEXT DEFAULT 'PENDING'")
    except:
        pass # Column likely exists

    # Migration: Check if 'preference' column exists in daily_workouts, if not add it
    try:
        con.execute("SELECT preference FROM daily_workouts LIMIT 1")
    except Exception:
        # print("Migrating: Adding 'preference' column to daily_workouts")
        con.execute("ALTER TABLE daily_workouts ADD COLUMN preference INTEGER DEFAULT 0")
        
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
    
    # Get the ID of the inserted row using the sequence
    plan_id = con.execute("SELECT currval('plan_id_seq')").fetchone()[0]
    
    con.close()
    print(f"Plan saved to DuckDB (ID: {plan_id}).")
    return plan_id

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
        con.close()

def save_analysis(content, context_json="{}"):
    """Saves a new trend analysis."""
    con = duckdb.connect(DB_FILE)
    timestamp = datetime.now()
    con.execute("INSERT INTO trend_analysis (timestamp, content, context_json) VALUES (?, ?, ?)", 
                (timestamp, content, context_json))
    con.close()

def get_latest_analysis():
    """Retrieves the most recent trend analysis."""
    con = duckdb.connect(DB_FILE)
    try:
        result = con.execute("""
            SELECT content, timestamp FROM trend_analysis 
            ORDER BY timestamp DESC 
            LIMIT 1
        """).fetchone()
    except:
        return None
    finally:
        con.close()
        
    if result:
        return {
            "content": result[0],
            "date": str(result[1])
        }
    return None

def save_daily_workouts(plan_id, workouts_data):
    """Saves individual daily workouts from the JSON plan."""
    con = duckdb.connect(DB_FILE)
    
    # workouts_data should be a list of dicts: [{'day': 1, 'activity': ...}, ...]
    for w in workouts_data:
        # Save as JSON string for flexibility
        content_json = json.dumps(w)
        day_offset = w.get('day', 1)
        
        con.execute("""
            INSERT INTO daily_workouts (plan_id, day_offset, content, status)
            VALUES (?, ?, ?, 'PENDING')
        """, (plan_id, day_offset, content_json))
        
    con.close()

def get_plan_workouts(plan_id):
    """Retrieves all daily workouts for a specific plan."""
    con = duckdb.connect(DB_FILE)
    try:
        results = con.execute("""
            SELECT id, day_offset, content, status, preference
            FROM daily_workouts 
            WHERE plan_id = ?
            ORDER BY day_offset ASC
        """, (plan_id,)).fetchall()
        
        workouts = []
        for r in results:
            workouts.append({
                "id": r[0],
                "day": r[1],
                "content": json.loads(r[2]), # Parse the JSON content back to dict
                "status": r[3],
                "preference": r[4] if r[4] is not None else 0
            })
        return workouts
    except Exception as e:
        print(f"Error fetching workouts: {e}")
        return []
    finally:
        con.close()

def update_workout_status(workout_id, new_status):
    con = duckdb.connect(DB_FILE)
    con.execute("UPDATE daily_workouts SET status = ? WHERE id = ?", (new_status, workout_id))
    con.close()

def update_workout_preference(workout_id, preference):
    """
    preference: 1 (Less), 2 (Neutral), 3 (More)
    """
    con = duckdb.connect(DB_FILE)
    con.execute("UPDATE daily_workouts SET preference = ? WHERE id = ?", (preference, workout_id))
    con.close()

def get_preference_history():
    """Returns a summary of liked/disliked workouts for AI context."""
    con = duckdb.connect(DB_FILE)
    
    # Get high rated (3 stars)
    liked = con.execute("""
        SELECT content FROM daily_workouts WHERE preference = 3 ORDER BY id DESC LIMIT 5
    """).fetchall()
    
    # Get low rated (1 star)
    disliked = con.execute("""
        SELECT content FROM daily_workouts WHERE preference = 1 ORDER BY id DESC LIMIT 5
    """).fetchall()
    
    con.close()
    
    def extract_summary(rows):
        summaries = []
        for r in rows:
            try:
                data = json.loads(r[0])
                # Prefer structure_summary, then activity
                txt = f"{data.get('activity', '?')} ({data.get('structure_summary', '')})" 
                summaries.append(txt)
            except:
                continue
        return summaries

    liked_list = extract_summary(liked)
    disliked_list = extract_summary(disliked)
    
    if not liked_list and not disliked_list:
        return ""
        
    return f"Käyttäjän toiveet: ENEMMÄN näitä: {', '.join(liked_list)}. VÄHEMMÄN näitä: {', '.join(disliked_list)}."

def get_calendar_events():
    """Retrieves all daily workouts formatted for streamlit-calendar."""
    con = duckdb.connect(DB_FILE)
    
    # Join daily_workouts with training_plans to calculate the actual date
    # timestamp is in training_plans.
    # We assume 'day_offset' is 1-based index from the start date (plan timestamp).
    # DuckDB date math: timestamp + INTERVAL (day_offset - 1) DAY
    
    query = """
        SELECT 
            w.id,
            w.content,
            w.status,
            p.timestamp + INTERVAL (w.day_offset - 1) DAY as workout_date
        FROM daily_workouts w
        JOIN training_plans p ON w.plan_id = p.id
    """
    
    try:
        results = con.execute(query).fetchall()
    except Exception as e:
        print(f"Calendar query error: {e}")
        con.close()
        return []
        
    con.close()
    
    events = []
    for r in results:
        wid = r[0]
        try:
            content = json.loads(r[1])
            activity = content.get('activity', 'Treeni')
            # maybe add length to title if available?
        except:
            activity = "Treeni"
            
        status = r[2]
        w_date = r[3] # datetime object
        
        # Format date as YYYY-MM-DD
        date_str = w_date.strftime('%Y-%m-%d')
        
        # Colors
        if status == 'DONE':
            color = '#4CAF50' # Green
            border = '#2E7D32'
        elif status == 'SKIPPED':
            color = '#EF5350' # Red
            border = '#C62828'
        else:
            color = '#42A5F5' # Blue
            border = '#1565C0'
            
        events.append({
            "title": activity,
            "start": date_str,
            "allDay": True,
            "backgroundColor": color,
            "borderColor": border,
            # Props for potential click handling
            "extendedProps": {
                "id": wid,
                "status": status,
                "description": content.get('description', '')
            }
        })
        
    return events

def get_compliance_stats(days=7):
    """Calculates compliance % separately for 'DONE' vs 'SKIPPED'."""
    con = duckdb.connect(DB_FILE)
    try:
        # JOIN isn't strictly necessary if we just look at daily_workouts and assume recent IDs are relevant,
        # but let's just grab the last N workouts.
        results = con.execute(f"""
            SELECT status FROM daily_workouts 
            ORDER BY id DESC 
            LIMIT {days}
        """).fetchall()
        
        if not results:
            return "Ei historiatietoja."
            
        total = len(results)
        done_count = sum(1 for r in results if r[0] == 'DONE')
        skipped_count = sum(1 for r in results if r[0] == 'SKIPPED')
        
        return f"Viim. {total} treeniä: {done_count} Tehty, {skipped_count} Väliin."
    except:
        return ""
    finally:
        con.close()
