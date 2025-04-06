import os
import re
import json
import asyncio
import traceback
import time
import requests
import streamlit as st

from config import GROQ_MODEL_VERSATILE, GROQ_MODEL_FAST
from models.skill_analyzer import SkillAnalyzer
from utils.dalle_visualizer import DalleVisualizer
from services.prompt_builders import (
    create_content_generation_prompt,
    create_simplification_prompt,
    create_syllable_breakdown_prompt,
    create_math_visualization_prompt,
    create_chunking_prompt,
    create_instruction_visualization_prompt,
    create_quiz_generation_prompt,
    create_quiz_question_adaptation_prompt,
    create_quiz_feedback_prompt
)


class AdaptLearnAssistant:
    def __init__(self, api_key=None, db=None, openai_api_key=None): 
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        assert self.api_key, "API key needed."
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.db = db
        self.skill_analyzer = SkillAnalyzer(self) if db else None
        self.dalle_visualizer = DalleVisualizer(api_key=openai_api_key) if openai_api_key else None
        
    def _send_request(self, model, messages, temperature=0.5, max_tokens=3072):
        """Send a request to the LLM API and return the response."""
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        try: 
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=90)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout: 
            st.error("API timeout.")
            return None
        except requests.exceptions.RequestException as e: 
            st.error(f"API fail: {e}")
            traceback.print_exc()
            return None
            
    def generate_content_from_topic(self, topic: str):
        """Generate educational content for a given topic."""
        sys_p, user_p = create_content_generation_prompt(topic)
        response = self._send_request(GROQ_MODEL_VERSATILE, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p}
        ], temperature=0.6)
        return response['choices'][0]['message']['content'] if response and 'choices' in response else None
        
    def structure_content_description(self, text: str):
        """Analyze and structure text to identify key points and organization."""
        sys_p = "Analyze text. ID topic, key points, instructions/questions."
        response = self._send_request(GROQ_MODEL_FAST, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"Structure:\n{text}"}
        ], temperature=0.2, max_tokens=1024)
        return response['choices'][0]['message']['content'] if response and 'choices' in response else text
        
    async def apply_adaptations_async(self, text: str, profile: dict):
        """Apply various adaptations to content based on user profile and needs."""
        adaptations = {}
        tasks = []
        keys = []
        
        if not text:
            return {}
            
        dis = profile.get("disability_type", "None")
        style = profile.get("learning_style", "Visual")
        
        async def run_task(key, model, sys_p, user_p, temp):
            # Fixed to use temperature parameter
            tasks.append(self._send_request_async(model, [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p}
            ], temperature=temp))
            keys.append(key)
            
        if dis == "Dyslexia":
            sys_p, user_p = create_simplification_prompt(text)
            await run_task("simplified_dyslexia", GROQ_MODEL_FAST, sys_p, user_p, 0.3)
            sys_p, user_p = create_syllable_breakdown_prompt(text)
            await run_task("syllable_breakdown", GROQ_MODEL_FAST, sys_p, user_p, 0.2)
            adaptations["dyslexia_ui_notes"] = "Suggest: OpenDyslexic font."
            
        if dis == "Dyscalculia":
            # Instead of using Mermaid for math visualization, use DALL-E
            if self.dalle_visualizer:
                # First, generate a brief text explanation
                sys_p = "Math tutor. Explain clearly (for Dyscalculia). Identify key math concept to visualize."
                user_p = f"Explain this math content clearly for someone with Dyscalculia. Also identify ONE key math concept that would benefit most from visualization:\n{text}\nExplanation:"
                
                response = self._send_request(GROQ_MODEL_FAST, [
                    {"role": "system", "content": sys_p},
                    {"role": "user", "content": user_p}
                ], temperature=0.4)
                
                if response and 'choices' in response and response['choices']:
                    explanation = response['choices'][0]['message']['content']
                    adaptations["math_visualization_text"] = explanation
                    
                    # Extract the key concept for visualization
                    concept_match = re.search(r"Key concept to visualize: (.*?)(?:\n|$)", explanation, re.IGNORECASE)
                    concept_to_visualize = concept_match.group(1) if concept_match else "mathematical concept from the text"
                    
                    # Generate visualization using DALL-E
                    visual_img = self.dalle_visualizer.visualize_mathematics(concept_to_visualize)
                    if visual_img:
                        # Save the image to a file
                        img_filename = f"math_visual_{int(asyncio.get_event_loop().time())}.png"
                        visual_img.save(img_filename)
                        adaptations["math_visualization_image"] = img_filename
            else:
                # Fallback to traditional text explanation if DALL-E is not available
                sys_p, user_p = create_math_visualization_prompt(text)
                await run_task("math_visualization", GROQ_MODEL_VERSATILE, sys_p, user_p, 0.5)
            
        if dis == "ADHD":
            chunk = profile.get("preferences", {}).get("chunk_size", 150)
            sys_p, user_p = create_chunking_prompt(text, chunk)
            await run_task("chunked_adhd", GROQ_MODEL_FAST, sys_p, user_p, 0.4)
            
        if dis == "Dysgraphia":
            adaptations["dysgraphia_support"] = "Suggest: LLM outlines."
            
        if dis == "Auditory Processing":
            # Use DALL-E for instruction visualization instead of Mermaid
            if self.dalle_visualizer:
                # First, identify what instructions need visualization
                sys_p = "Instructional designer. Identify key instructions that would benefit from visual representation."
                user_p = f"Identify the most important instructions or steps from this text that would benefit from visual representation:\n{text}\nKey instructions to visualize:"
                
                response = self._send_request(GROQ_MODEL_FAST, [
                    {"role": "system", "content": sys_p},
                    {"role": "user", "content": user_p}
                ], temperature=0.4)
                
                if response and 'choices' in response and response['choices']:
                    instruction_text = response['choices'][0]['message']['content']
                    adaptations["instruction_visualization_text"] = instruction_text
                    
                    # Generate visualization using DALL-E
                    visual_img = self.dalle_visualizer.visualize_instructions(instruction_text)
                    if visual_img:
                        # Save the image to a file
                        img_filename = f"instruction_visual_{int(asyncio.get_event_loop().time())}.png"
                        visual_img.save(img_filename)
                        adaptations["instruction_visualization_image"] = img_filename
            else:
                # Fallback to traditional text explanation if DALL-E is not available
                sys_p, user_p = create_instruction_visualization_prompt(text)
                await run_task("instruction_visualization", GROQ_MODEL_VERSATILE, sys_p, user_p, 0.5)
                
            adaptations["ap_support"] = "Suggest: TTS w/ highlight."
            
        if style == "Reading/Writing" and "simplified_dyslexia" not in keys:
            sys_p, user_p = create_simplification_prompt(text, "concise summary")
            await run_task("summary_rw", GROQ_MODEL_FAST, sys_p, user_p, 0.3)
            
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, res in enumerate(results):
                k = keys[i]
                if isinstance(res, Exception):
                    st.warning(f"Failed '{k}': {res}")
                elif res and 'choices' in res and res['choices']:
                    adaptations[k] = res['choices'][0]['message']['content']
                else:
                    st.warning(f"No content for: {k}")
                    
        # Generate a general concept visualization for Visual learners
        if style == "Visual" and self.dalle_visualizer:
            # First, identify what concept should be visualized
            sys_p = "Educational content analyst. Identify the most important concept to visualize for a visual learner."
            user_p = f"Identify the most important concept from this text that would benefit from visualization for a visual learner:\n{text}\nConcept to visualize:"
            
            response = self._send_request(GROQ_MODEL_FAST, [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p}
            ], temperature=0.4)
            
            if response and 'choices' in response and response['choices']:
                concept_text = response['choices'][0]['message']['content']
                adaptations["concept_visualization_text"] = concept_text
                
                # Generate visualization using DALL-E
                visual_img = self.dalle_visualizer.visualize_concept(concept_text, context=text[:500])
                if visual_img:
                    # Save the image to a file
                    img_filename = f"concept_visual_{int(asyncio.get_event_loop().time())}.png"
                    visual_img.save(img_filename)
                    adaptations["concept_visualization_image"] = img_filename
                
            adaptations["visual_learner_note"] = "Suggest: visual aids and diagrams."
        elif style == "Visual" and not any(k in adaptations for k in ["math_visualization_image", "concept_visualization_image", "instruction_visualization_image"]):
            adaptations["visual_learner_note"] = "Suggest: diagrams."
            
        if style == "Auditory":
            adaptations["auditory_learner_note"] = "Suggest: TTS (Omitted)."
            
        if style == "Kinesthetic":
            adaptations["kinesthetic_learner_note"] = "Suggest: interactive."
            
        if "chunked_adhd" in adaptations: # Parse the chunks from numbered list format
            raw = adaptations["chunked_adhd"]
            parsed = []
            lines = raw.split('\n')
            current = ""
            num = 1
            
            for line in lines:
                strip = line.strip()
                match = re.match(r"^\d+[\.\)\s]+", strip)
                if match:
                    if current:
                        parsed.append(current.strip())
                    current = strip[match.end():].strip()
                    num += 1
                elif current:
                    current += "\n" + line
                    
            if current:
                parsed.append(current.strip())
                
            if parsed:
                adaptations["chunked_adhd"] = parsed
            else:
                st.warning("Chunk parsing failed")
                adaptations["chunked_adhd_raw"] = raw
                del adaptations["chunked_adhd"]
                
        return adaptations
        
    async def _send_request_async(self, model, messages, temperature=0.5, max_tokens=3072): 
        """Async version of _send_request."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self._send_request(model, messages, temperature, max_tokens)
        )
        return response
        
    def generate_recommendations_text(self, user_id):
        """Generate personalized learning recommendations based on user's weak skills."""
        if not self.db:
            return "Database unavailable."
            
        weak = self.db.get_user_weakest_skills(user_id, 3)
        if not weak:
            return "No weak areas identified!"
            
        skills = ", ".join([f"'{n}'" for _, n, _, _ in weak])
        sys_p = "Advisor: 1. Focus areas. 2. Next content/topics. 3. Strategies."
        response = self._send_request(GROQ_MODEL_VERSATILE, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"Weak: {skills}. Recs?"}
        ], temperature=0.6)
        return response['choices'][0]['message']['content'] if response and 'choices' in response else "Recommendations failed."
        
    def generate_personalized_learning_path(self, user_id, focus_skills_str, num_steps=5):
        """Generate a personalized learning path based on focus skills."""
        if not self.db:
            return None, "Database unavailable."
            
        sys_p = f"Designer: Create {num_steps}-step path for: {focus_skills_str}. Step: title, objective, content suggestion. Numbered list."
        response = self._send_request(GROQ_MODEL_VERSATILE, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"Gen path: {focus_skills_str}."}
        ], temperature=0.5)
        
        if response and 'choices' in response:
            path_text = response['choices'][0]['message']['content']
            path_title = f"Path: {focus_skills_str[:50]}"
            path_desc = f"Focus: {focus_skills_str}."
            path_id = self.db.create_learning_path(user_id, path_title, path_desc, focus_skills_str)
            return path_id, path_text
        else:
            return None, "Path generation failed."
            
    def identify_content_skills(self, content_text):
        """Identify skills present in content with their relevance scores."""
        return self.skill_analyzer.analyze_content(content_text) if self.skill_analyzer else {}
        
    def get_analysis_and_recommendations(self, user_id):
        """Get comprehensive analysis and recommendations based on user skills."""
        if not self.db:
            return None
            
        weak = self.db.get_user_weakest_skills(user_id, 3)
        strong = self.db.get_user_strongest_skills(user_id, 3)
        
        if not weak and not strong:
            return None
            
        strong_s = ", ".join([f"'{n}' ({p:.1f})" for _, n, _, p in strong]) or "N/A"
        weak_s = ", ".join([f"'{n}' ({p:.1f})" for _, n, _, p in weak]) or "N/A"
        
        sys_p = "Analyst: 1. Strengths/weaknesses. 2. Actionable recs for weak. 3. Leverage strengths."
        response = self._send_request(GROQ_MODEL_VERSATILE, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"Str: {strong_s}\nWeak: {weak_s}\nAnalysis?"}
        ], temperature=0.4)
        
        analysis = response['choices'][0]['message']['content'] if response and 'choices' in response else "Analysis failed."
        return {"analysis_text": analysis, "weak_skills": weak, "strong_skills": strong}
    
    # --- Quiz Generation Methods ---
    def generate_quiz(self, user_id, topic, difficulty, num_questions=5):
        """Generate a quiz with adaptations for user's learning style and needs."""
        if not self.db:
            return None, "Database unavailable."
            
        # Get user's profile for adaptations
        user_profile = self.db.get_user_profile(user_id)
        
        # Create quiz prompts
        sys_p, user_p = create_quiz_generation_prompt(topic, difficulty, user_profile, num_questions)
        
        # Generate quiz content
        response = self._send_request(GROQ_MODEL_VERSATILE, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p}
        ], temperature=0.7, max_tokens=4000)
        
        if not response or 'choices' not in response:
            return None, "Quiz generation failed."
            
        try:
            # Extract JSON from response
            content = response['choices'][0]['message']['content']
            
            # In case there's surrounding text, extract just the JSON portion
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            match = re.search(json_pattern, content)
            if match:
                json_str = match.group(1)
            else:
                json_str = content
                
            # Try to find json content with {} pattern if above doesn't work
            if not json_str.strip().startswith('{'):
                match = re.search(r'\{[\s\S]*\}', json_str)
                if match:
                    json_str = match.group(0)
            
            # Parse the JSON
            quiz_data = json.loads(json_str)
            
            # Save quiz to database - FIXED: Convert all values to strings
            quiz_title = str(quiz_data.get('title', f"Quiz on {topic}"))
            quiz_description = str(quiz_data.get('description', f"A {difficulty} difficulty quiz about {topic}"))
            quiz_topic = str(topic)
            quiz_difficulty = str(difficulty)
            
            quiz_id = self.db.create_quiz(
                user_id,
                quiz_title,
                quiz_description,
                quiz_topic,
                quiz_difficulty
            )
            
            # Get skills to associate with questions
            skill_names = {}
            for idx, question in enumerate(quiz_data.get('questions', [])):
                skill_name = question.get('skill', '')
                if skill_name:
                    skill_names[skill_name] = {'position': idx}
            
            # Analyze skills to get IDs where possible
            skill_map = {}
            if skill_names:
                cur = self.db.conn.cursor()
                
                # Try to find existing skills or create new ones
                for skill_name, data in skill_names.items():
                    cur.execute('SELECT skill_id FROM skills WHERE name = ?', (skill_name,))
                    result = cur.fetchone()
                    
                    if result:
                        skill_map[skill_name] = {'skill_id': result[0], 'position': data['position']}
                    else:
                        # Determine category based on keywords
                        category = "general"
                        if any(kw in skill_name.lower() for kw in ["math", "algebra", "calc", "geom"]):
                            category = "math"
                        elif any(kw in skill_name.lower() for kw in ["program", "code", "data", "algo", "loop", "func"]):
                            category = "programming"
                        elif any(kw in skill_name.lower() for kw in ["comprehen", "read", "idea", "seq", "summar"]):
                            category = "comprehension"
                        elif any(kw in skill_name.lower() for kw in ["vocab", "word", "language", "grammar"]):
                            category = "language"
                        elif any(kw in skill_name.lower() for kw in ["science", "biology", "physics", "chemistry"]):
                            category = "science"
                            
                        # Create the skill
                        try:
                            cur.execute('INSERT INTO skills (name, category) VALUES (?, ?)', (skill_name, category))
                            skill_id = cur.lastrowid
                            skill_map[skill_name] = {'skill_id': skill_id, 'position': data['position']}
                        except Exception as e:
                            print(f"Error creating skill {skill_name}: {e}")
                            
                self.db.conn.commit()
            
            # Save questions to database
            for idx, question in enumerate(quiz_data.get('questions', [])):
                # Get question details
                question_text = question.get('question_text', '')
                question_type = question.get('question_type', 'Multiple Choice')
                options = question.get('options', [])
                correct_answer = question.get('correct_answer', '')
                explanation = question.get('explanation', '')
                
                # Determine adaptation type based on user profile
                adaptation_type = None
                if user_profile.get('disability_type') != 'None':
                    adaptation_type = user_profile.get('disability_type')
                elif user_profile.get('learning_style') != 'Visual':  # Default is visual
                    adaptation_type = user_profile.get('learning_style')
                
                # Get skill_id if available
                skill_name = question.get('skill', '')
                skill_id = None
                if skill_name in skill_map:
                    skill_id = skill_map[skill_name]['skill_id']
                
                # Add question to database
                self.db.add_quiz_question(
                    quiz_id=quiz_id,
                    question_text=question_text,
                    question_type=question_type,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    adaptation_type=adaptation_type,
                    skill_id=skill_id,
                    position=idx
                )
            
            return quiz_id, "Quiz created successfully!"
            
        except Exception as e:
            print(f"Error processing quiz data: {e}")
            traceback.print_exc()
            return None, f"Error creating quiz: {str(e)}"
    
    def adapt_quiz_question(self, question_data, user_profile):
        """Adapt a quiz question to better suit the user's learning style and needs."""
        sys_p, user_p = create_quiz_question_adaptation_prompt(question_data, user_profile)
        
        response = self._send_request(GROQ_MODEL_FAST, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p}
        ], temperature=0.5)
        
        if not response or 'choices' not in response:
            return question_data
        
        try:
            # Extract JSON from response
            content = response['choices'][0]['message']['content']
            
            # Try to find json content
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                adaptation = json.loads(match.group(0))
                
                # Create adapted question
                adapted_question = question_data.copy()
                
                if 'adapted_question' in adaptation:
                    adapted_question['question_text'] = adaptation['adapted_question']
                
                if 'adapted_options' in adaptation and adaptation['adapted_options']:
                    adapted_question['options'] = adaptation['adapted_options']
                    
                    # Make sure correct answer is still in options
                    if adapted_question['correct_answer'] not in adapted_question['options']:
                        # Find the most similar option or use the first one
                        adapted_question['correct_answer'] = adapted_question['options'][0]
                
                if 'adaptation_notes' in adaptation:
                    adapted_question['adaptation_notes'] = adaptation['adaptation_notes']
                
                return adapted_question
            
        except Exception as e:
            print(f"Error adapting question: {e}")
        
        # Return original if adaptation fails
        return question_data
    
    def generate_quiz_feedback(self, attempt_results, user_profile):
        """Generate personalized feedback for a quiz attempt."""
        sys_p, user_p = create_quiz_feedback_prompt(attempt_results, user_profile)
        
        response = self._send_request(GROQ_MODEL_VERSATILE, [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p}
        ], temperature=0.6)
        
        if not response or 'choices' not in response:
            # Default feedback if generation fails
            score = attempt_results.get('score', 0)
            max_score = attempt_results.get('max_score', 0)
            success_rate = score / max_score if max_score > 0 else 0
            
            if success_rate >= 0.8:
                return "Excellent work! You demonstrated a strong understanding of the material."
            elif success_rate >= 0.6:
                return "Good job! You're making progress. Review the questions you missed to improve further."
            else:
                return "Keep practicing! Review the material and try again to strengthen your understanding."
        
        return response['choices'][0]['message']['content']
    
    # --- DALL-E Visualization Methods ---
    def generate_visualization(self, concept, context=None):
        """Generate a visualization using DALL-E for a concept."""
        if not self.dalle_visualizer:
            return None, "DALL-E API key not provided. Unable to generate visualization."
            
        try:
            image = self.dalle_visualizer.visualize_concept(concept, context)
            if image:
                # Save the image to a file
                img_filename = f"visualization_{int(time.time())}.png"
                image.save(img_filename)
                return img_filename, "Visualization generated successfully."
            else:
                return None, "Failed to generate visualization."
        except Exception as e:
            return None, f"Error generating visualization: {str(e)}"