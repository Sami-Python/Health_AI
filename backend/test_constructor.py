from garminconnect import Garmin
from unittest.mock import patch, MagicMock

def test_constructor():
    print("Testing Garmin constructor behavior...")
    with patch("requests.Session.get") as mock_get, \
         patch("requests.Session.post") as mock_post:
        
        mock_get.return_value = MagicMock(status_code=200, text="mock")
        
        client = Garmin("user", "pass")
        print(f"GET called: {mock_get.called}")
        print(f"POST called: {mock_post.called}")

if __name__ == "__main__":
    test_constructor()
