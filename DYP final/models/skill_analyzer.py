import re
import json
from config import GROQ_MODEL_FAST

class SkillAnalyzer:
    def __init__(self, assistant): 
        self.assistant = assistant
        
    def analyze_content(self, content_text):
        """
        Analyzes content to identify relevant skills and their relevance scores.
        Returns a dictionary of {skill_name: relevance_score} where scores are between 0.0 and 1.0.
        """
        sys_p="Analyze text: 1. ID skills/concepts (comprehension, subject, logic, vocab). 2. Rate relevance (0-1). 3. Return ONLY JSON {skill: score}."
        msgs=[{"role":"system","content":sys_p},{"role":"user","content":f"Analyze:\n{content_text}"}]
        # Fixed: use temperature instead of temp, and max_tokens instead of max_t
        response=self.assistant._send_request(GROQ_MODEL_FAST, msgs, temperature=0.1, max_tokens=500)
        
        if response and 'choices' in response and response['choices']:
            content=response['choices'][0]['message']['content']
            try: 
                match=re.search(r'\{[\s\S]*\}', content)
                if match: 
                    parsed=json.loads(match.group(0))
                    return {k: max(0.0, min(1.0, float(v))) for k, v in parsed.items() if isinstance(k, str) and isinstance(v, (int, float))}
            except Exception as e: 
                print(f"Error parsing skills: {e}")
                return {}
                
        return {}