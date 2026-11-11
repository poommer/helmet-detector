# 
import json
from pathlib import Path 

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "line_subscribers.json"

# อ่านรายชื่อของ follower - that user 
def get_subscribers():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True) 

    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8") 

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file) 


# add user when add friend 
def add_subscriber(user_id: str): 
    subscribers = get_subscribers() 

    if user_id not in subscribers: 
        subscribers.append(user_id) 

        with DATA_FILE.open("w", encoding="utf-8") as file: 
            json.dump(
                subscribers,
                file, 
                ensure_ascii=False,
                indent=4
            )

# delete user when block bot 
def remove_subscriber(user_id: str): 
    subscribers = get_subscribers() 

    if user_id in subscribers: 

        with DATA_FILE.open("w", encoding="utf-8") as file: 
            json.dump(
                subscribers, 
                file, 
                ensure_ascii=False, 
                indent=4
            )