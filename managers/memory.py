import collections
import time

class MemoryManager:
    def __init__(self, max_history=10):
        # user_id -> deque of messages
        self.history = collections.defaultdict(lambda: collections.deque(maxlen=max_history))
        # user_id -> dict of "facts" or metadata
        self.metadata = collections.defaultdict(dict)

    def add_message(self, user_id, role, content):
        self.history[user_id].append({"role": role, "content": content, "timestamp": time.time()})

    def get_history(self, user_id):
        return list(self.history[user_id])

    def clear_history(self, user_id):
        self.history[user_id].clear()

    def set_metadata(self, user_id, key, value):
        self.metadata[user_id][key] = value

    def get_metadata(self, user_id, key=None):
        if key:
            return self.metadata[user_id].get(key)
        return self.metadata[user_id]
