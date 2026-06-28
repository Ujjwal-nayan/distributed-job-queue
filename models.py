import uuid
from datetime import datetime

def generate_id():
    return str(uuid.uuid4())

class Job:
    def __init__(self, payload, max_retries=3):
        self.id = generate_id()
        self.status = "pending"
        self.payload = payload
        self.retry_count = 0
        self.max_retries = max_retries
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.error_message = None

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "payload": self.payload,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "error_message": self.error_message
        }
