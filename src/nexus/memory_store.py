"""
memory_store.py
----------------
A very simple "memory" for our agent. In a real product this would be a
vector database (Chroma / Pinecone). Here it's just a Python list, so
it's easy to see what's happening.

Every memory entry has:
  - content: the fact being stored
  - source: where this fact came from (user, tool_output, agent_reasoning)
This "source" field is exactly what our Memory Write Gate will check.
"""

class MemoryStore:
    def __init__(self):
        self.entries = []

    def write(self, content: str, source: str):
        entry = {"content": content, "source": source}
        self.entries.append(entry)
        print(f"[MEMORY] Wrote entry: {entry}")
        return entry

    def all_entries(self):
        return self.entries

    def find_contradictions(self, new_content: str):
        """
        VERY simple contradiction check for demo purposes.
        Real version would use an LLM or embeddings to compare meaning.
        Here we just check for a couple of known opposite facts.
        """
        contradictions = []
        for entry in self.entries:
            old = entry["content"].lower()
            new = new_content.lower()
            # toy example: conflicting locations
            if "lahore" in old and "tokyo" in new:
                contradictions.append(entry)
            if "tokyo" in old and "lahore" in new:
                contradictions.append(entry)
        return contradictions
