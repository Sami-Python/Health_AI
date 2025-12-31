import pytest
import os
import db_manager
from datetime import datetime

# Use a temporary DB file for testing
TEST_DB = "test_health_ai.db"

@pytest.fixture(autouse=True)
def run_around_tests():
    """Sets up and tears down the test database."""
    # Setup
    db_manager.set_db_path(TEST_DB)
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db_manager.init_db()
    
    yield
    
    # Teardown
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_db_init():
    """Verifies that tables are created."""
    assert os.path.exists(TEST_DB)

def test_add_and_get_goal():
    """Test adding and retrieving a goal."""
    db_manager.add_goal("Juoksu", "50 km", datetime.now(), "Test Goal")
    goals = db_manager.get_active_goals()
    
    assert len(goals) == 1
    assert goals[0]['type'] == "Juoksu"
    assert goals[0]['target'] == "50 km"

def test_log_manual_workout():
    """Test logging a manual workout."""
    db_manager.log_manual_workout(datetime.now(), "Kuntosali", 60, 8, "Hard session")
    
    stats = db_manager.get_weekly_stats()
    # Find today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Manual load should be 60 * 8 = 480
    assert stats[today]['manual'] == 480
