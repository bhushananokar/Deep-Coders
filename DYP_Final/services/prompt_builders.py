def create_content_generation_prompt(topic: str): 
    """Creates a prompt for generating educational content on a topic."""
    sys_p="Educator: Generate HS/UG content. Structure logically. Explain jargon."
    user_p=f"Generate content: **{topic}**. ~3-5 paras."
    return sys_p, user_p
    
def create_learning_path_prompt(topic: str): 
    """Creates a prompt for generating a learning path on a topic."""
    sys_p="Curriculum designer (STEM): Create 5-10 step path. Each step: title, concept desc. Numbered list."
    user_p=f"Generate path for STEM topic: **{topic}**."
    return sys_p, user_p
    
def create_simplification_prompt(text: str, level: str="simpler"): 
    """Creates a prompt for simplifying text."""
    prompt=f"Simplify (easy understand, short sentences, explain terms). Level: {level}.\nTxt:\n{text}\nSimplified:"
    return "Text simplifier.", prompt
    
def create_chunking_prompt(text: str, size: int=150): 
    """Creates a prompt for breaking text into smaller chunks."""
    prompt=f"Break into chunks (~{size} words). Numbered list '1.'.\nTxt:\n{text}\nChunked:"
    return "Info organizer.", prompt
    
def create_syllable_breakdown_prompt(text: str): 
    """Creates a prompt for breaking down complex words into syllables."""
    prompt=f"ID complex words (3+ syll). Hyphenate.\nTxt:\n{text}\nBreakdown:"
    return "Linguist.", prompt
    
def create_math_visualization_prompt(text: str): 
    """Creates a prompt for visualizing math concepts using Mermaid diagrams when appropriate."""
    prompt=f"Analyze math: 1. Explain clearly (Dyscalculia). 2. Eval if simple Mermaid helps. 3. **If valuable**, gen Mermaid code. 4. **Else: no Mermaid**.\nTxt:\n{text}\nAnalysis (Explain & Mermaid if helpful):"
    return "Math tutor. Use Mermaid judiciously.", prompt
    
def create_instruction_visualization_prompt(text: str): 
    """Creates a prompt for visualizing instructions using Mermaid diagrams when appropriate."""
    prompt=f"Analyze instructions: 1. Is sequence clear? 2. **If viz helps & suits simple Mermaid `graph TD`**, gen code. 3. **Else: No Mermaid**.\nInstr:\n{text}\nAnalysis (Mermaid only if valuable):"
    return "Instructional designer. Mermaid only if valuable.", prompt

def create_quiz_generation_prompt(topic: str, difficulty: str, user_profile: dict, num_questions: int=5):
    """Creates a prompt for generating a quiz with adaptations for user's learning needs."""
    learning_style = user_profile.get("learning_style", "Visual")
    disability_type = user_profile.get("disability_type", "None")
    
    adaptation_str = ""
    if disability_type != "None":
        adaptation_str += f"This quiz is for someone with {disability_type}. "
        
        if disability_type == "Dyslexia":
            adaptation_str += "Use simple language, clear fonts, and avoid cluttered presentation. For multiple choice, limit options to 3-4 choices. "
        elif disability_type == "Dyscalculia":
            adaptation_str += "For math questions, break down problems into clear steps. Include visual representations when possible. "
        elif disability_type == "ADHD":
            adaptation_str += "Keep questions concise and focused. Break multi-part questions into separate items. "
        elif disability_type == "Dysgraphia":
            adaptation_str += "Prefer multiple choice and structured response formats over open-ended writing. "
        elif disability_type == "Auditory Processing":
            adaptation_str += "Emphasize visual cues and written instructions. Avoid questions that rely heavily on sound-alike words or audio interpretation. "
    
    adaptation_str += f"The user's primary learning style is {learning_style}. "
    
    if learning_style == "Visual":
        adaptation_str += "Include diagrams, charts or visualizations where appropriate. "
    elif learning_style == "Auditory":
        adaptation_str += "Frame questions in terms of verbal descriptions and discussions. "
    elif learning_style == "Kinesthetic":
        adaptation_str += "Include practical, hands-on examples and real-world applications. "
    elif learning_style == "Reading/Writing":
        adaptation_str += "Use well-structured text explanations and definitions. "
    
    system_prompt = (
        f"You are an expert educational assessment designer specializing in creating adaptive quizzes. "
        f"Create a quiz that tests understanding of the topic effectively while accommodating specific learning needs."
    )
    
    user_prompt = (
        f"Create a {difficulty} difficulty quiz about '{topic}' with exactly {num_questions} questions.\n\n"
        f"{adaptation_str}\n\n"
        f"For each question provide:\n"
        f"1. Question text\n"
        f"2. Question type (Multiple Choice, True/False, Short Answer)\n"
        f"3. Options (for Multiple Choice) - list 3-4 choices with the correct one indicated\n"
        f"4. Correct answer\n"
        f"5. Explanation for why that's the correct answer\n"
        f"6. Which specific skill this question tests (e.g., \"Understanding cause-effect\", \"Application of formula\", \"Analysis of text\")\n\n"
        f"Format the quiz as a well-structured JSON object with the following format:\n"
        f"{{\"title\": \"Quiz Title\", \"description\": \"Brief description\", \"questions\": [{{question objects}}]}}\n\n"
        f"For each question object, use: {{\"question_text\": \"\", \"question_type\": \"\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct_answer\": \"\", \"explanation\": \"\", \"skill\": \"\"}}\n\n"
        f"For True/False questions, options should be [\"True\", \"False\"].\n"
        f"For Short Answer questions, omit the 'options' field.\n\n"
        f"Only return valid JSON. Ensure the correct_answer for multiple choice questions exactly matches one of the options."
    )
    
    return system_prompt, user_prompt

def create_quiz_question_adaptation_prompt(question_data: dict, user_profile: dict):
    """Creates a prompt for adapting a specific quiz question to user's learning style and needs."""
    question_text = question_data.get('question_text', '')
    question_type = question_data.get('question_type', '')
    options = question_data.get('options', [])
    learning_style = user_profile.get('learning_style', 'Visual')
    disability_type = user_profile.get('disability_type', 'None')
    
    system_prompt = (
        "You are an expert in educational accessibility. Adapt learning content to "
        "better suit different learning styles and accommodate specific learning needs."
    )
    
    user_prompt = (
        f"Adapt this quiz question for a learner with {learning_style} learning style"
        f"{' and ' + disability_type if disability_type != 'None' else ''}:\n\n"
        f"Original Question: {question_text}\n"
        f"Type: {question_type}\n"
        f"Options: {options if options else 'None'}\n\n"
        f"Please provide an adapted version that maintains the same difficulty and tests "
        f"the same concept, but makes it more accessible for this learner's profile.\n\n"
        f"Return a JSON object with these fields:\n"
        f"{{\"adapted_question\": \"The adapted question text\", "
        f"\"adapted_options\": [\"A\", \"B\", \"C\"] if applicable, "
        f"\"adaptation_notes\": \"Brief notes on what was changed and why\"}}"
    )
    
    return system_prompt, user_prompt

def create_quiz_feedback_prompt(quiz_results: dict, user_profile: dict):
    """Creates a prompt for generating personalized quiz feedback."""
    system_prompt = (
        "You are an insightful educational coach who provides constructive, supportive "
        "feedback on quiz performance. Your feedback highlights strengths, identifies "
        "areas for improvement, and offers tailored learning strategies."
    )
    
    score = quiz_results.get('score', 0)
    max_score = quiz_results.get('max_score', 0)
    success_rate = quiz_results.get('success_rate', 0)
    questions = quiz_results.get('questions', [])
    
    # Build question summaries
    question_summary = ""
    correct_count = 0
    for i, q in enumerate(questions):
        result = "✓" if q.get('is_correct') else "✗"
        correct_count += 1 if q.get('is_correct') else 0
        question_summary += f"Q{i+1}: {result} - {q.get('question_text', '')[:50]}...\n"
    
    learning_style = user_profile.get('learning_style', 'Visual')
    disability_type = user_profile.get('disability_type', 'None')
    
    user_prompt = (
        f"Provide encouraging, constructive feedback for a quiz with score: {score}/{max_score} ({success_rate*100:.1f}%).\n\n"
        f"Questions summary:\n{question_summary}\n"
        f"The learner's primary style is {learning_style}"
        f"{' with ' + disability_type if disability_type != 'None' else ''}.\n\n"
        f"In your feedback:\n"
        f"1. Begin with a positive, encouraging statement noting their achievements\n"
        f"2. Mention 2-3 specific improvement areas based on incorrect questions\n"
        f"3. Suggest 2-3 concrete study strategies tailored to their learning style\n"
        f"4. End with a motivational closing that encourages continuing to learn\n\n"
        f"Keep your feedback supportive, specific, and actionable. Maximum 300 words."
    )
    
    return system_prompt, user_prompt