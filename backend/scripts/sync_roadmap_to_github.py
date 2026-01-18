import os
import re
import requests
import sys
from dotenv import load_dotenv

# Force UTF-8 encoding for Windows terminal output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python
        pass

# Find the project root (assuming script is in backend/scripts)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))

# Load environment variables from root .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

def clean_text(text):
    # Remove emojis and other non-standard characters
    return re.sub(r'[^\x00-\x7F]+', '', text).strip()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "Sami-Python/Health_AI"
ROADMAP_PATH = os.path.join(PROJECT_ROOT, "Docs/production_roadmap.md")
API_BASE = "https://api.github.com"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def create_github_issue(title, body, labels=None, closed=False):
    url = f"{API_BASE}/repos/{REPO}/issues"
    data = {
        "title": title,
        "body": body,
        "labels": labels or []
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        issue_data = response.json()
        issue_number = issue_data["number"]
        print(f"Created issue #{issue_number}: {title}")
        
        if closed:
            close_url = f"{API_BASE}/repos/{REPO}/issues/{issue_number}"
            close_data = {"state": "closed"}
            requests.patch(close_url, json=close_data, headers=headers)
            print(f"Closed issue #{issue_number}")
            
        return issue_number
    else:
        print(f"Error creating issue: {response.status_code}")
        print(response.text)
        return None

def sync():
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN not found in .env")
        return

    with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    current_section = "Roadmap"
    
    # Regex for task lines: - [x] **Title** (Context)
    # We look for [x], [ ], [/], [-]
    task_pattern = re.compile(r"^(\s*)-\s\[([x\-\/ \+])] (.*)")
    issue_num_pattern = re.compile(r"\(#\d+\)")

    print(f"Syncing roadmap from {ROADMAP_PATH} to {REPO}...")

    for line in lines:
        # Detect sections
        if line.startswith("## "):
            current_section = line.strip("# ").strip()
        
        match = task_pattern.match(line)
        if match:
            indent = match.group(1)
            status_char = match.group(2)
            task_content = match.group(3).strip()
            
            # Skip if issue number already exists
            if issue_num_pattern.search(task_content):
                updated_lines.append(line)
                continue
            
            # Clean title: Remove markdown bolding if present
            clean_title = task_content.replace("**", "").split("(")[0].strip()
            clean_title = clean_text(clean_title)
            
            # Labels: Current section
            label = current_section.split(".")[0].strip() # e.g. "1" or "3.4 Garmin..."
            label = clean_text(label)
            labels = [label] if label else []
            
            # Additional label from content if any (e.g. Phase 7)
            if "Phase" in current_section:
                phase_label = current_section.split(":")[0].strip()
                labels.append(clean_text(phase_label))
            
            # Determine if it should be closed
            is_closed = status_char in ["x", "-", "+"] # x is done, - is skip, + is done
            
            # Create the issue
            issue_num = create_github_issue(
                title=f"{clean_title}",
                body=f"Task from roadmap section: {current_section}\n\nOriginal text: {task_content}",
                labels=labels,
                closed=is_closed
            )
            if issue_num:
                # Update the line to include issue number
                new_line = line.rstrip() + f" (#{issue_num})\n"
                updated_lines.append(new_line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Write back the updated roadmap
    with open(ROADMAP_PATH, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)
    
    print("Sync complete.")

if __name__ == "__main__":
    sync()
