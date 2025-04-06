import time
import streamlit as st
import json
# Assuming these helpers exist and work as intended
try:
    from utils.helpers import extract_mermaid_code
except ImportError:
    st.error("Helper function 'extract_mermaid_code' not found. Please ensure utils/helpers.py exists.")
    # Define a dummy function to avoid NameError later
    def extract_mermaid_code(text): return None
try:
    from ui.rendering import render_mermaid
except ImportError:
    st.error("UI function 'render_mermaid' not found. Please ensure ui/rendering.py exists.")
    # Define a dummy function
    def render_mermaid(code): st.code(code, language='mermaid')


# --- Main Render Function ---

def render(db, assistant):
    """Render the main quiz page with tabs."""
    st.title("📝 Quizzes")

    # Ensure user_id is in session state
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.error("User not logged in or user ID is missing. Please log in again.")
        st.stop() # Halt execution if no user ID

    # Set up tabs
    tab_titles = ["Take Quiz", "Create Quiz", "My Quizzes"]
    tab1, tab2, tab3 = st.tabs(tab_titles)

    with tab1:
        st.header("Take a Quiz")
        # Logic to determine if showing selection, active quiz, or results
        if "current_quiz_id" in st.session_state and "current_attempt_id" in st.session_state:
            render_active_quiz(db, assistant)
        elif "quiz_result_id" in st.session_state:
            render_quiz_results(db, assistant)
        else:
            render_quiz_selection(db)

    with tab2:
        st.header("Create a New Quiz")
        render_create_quiz_form(db, assistant)

    with tab3:
        st.header("My Quizzes Overview")
        render_my_quizzes_tab(db)


# --- Helper Rendering Functions ---

def render_quiz_selection(db):
    """Renders the UI for selecting a quiz to take."""
    st.subheader("Recommended Quizzes")
    try:
        # Ensure user_id exists before calling DB function
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.warning("Cannot load recommendations: User ID missing.")
            recommended_quizzes = []
        else:
            recommended_quizzes = db.get_recommended_quizzes(user_id)
    except AttributeError:
        st.error("Database object does not have the method 'get_recommended_quizzes'.")
        recommended_quizzes = []
    except Exception as e:
        st.error(f"Failed to load recommended quizzes: {e}")
        recommended_quizzes = []

    if recommended_quizzes:
        for i, quiz in enumerate(recommended_quizzes):
            quiz_id = quiz.get('quiz_id')
            if not quiz_id: continue # Skip if quiz ID is missing
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{quiz.get('title', 'No Title')}**")
                st.markdown(f"*Topic: {quiz.get('topic', 'N/A')} • Difficulty: {quiz.get('difficulty', 'N/A')}*")
                st.markdown(f"{quiz.get('description', 'No Description')}")
            with col2:
                if st.button("Start Quiz", key=f"start_rec_quiz_{quiz_id}"):
                    if start_quiz(db, quiz_id): # Check if start was successful
                        st.rerun()
    else:
        st.info("No recommended quizzes found right now.")

    # Show all available quizzes
    with st.expander("All Available Quizzes", expanded=False):
        st.subheader("All Quizzes You Haven't Completed")
        quizzes = []
        try:
            user_id = st.session_state.get('user_id')
            if not user_id:
                st.warning("Cannot load quizzes: User ID missing.")
            else:
                # This assumes db.conn exists and works
                cur = db.conn.cursor()
                # Use placeholders to prevent SQL injection
                sql = '''
                    SELECT quiz_id, title, description, topic, difficulty
                    FROM quizzes
                    WHERE quiz_id NOT IN (
                        SELECT quiz_id FROM quiz_attempts
                        WHERE user_id = ? AND completed = 1
                    )
                    ORDER BY created_at DESC
                '''
                cur.execute(sql, (user_id,))
                # Fetch results into a list of dictionaries
                columns = [column[0] for column in cur.description]
                quizzes = [dict(zip(columns, row)) for row in cur.fetchall()]
        except AttributeError:
             st.error("Database connection (`db.conn`) or cursor method not available.")
        except Exception as e:
            st.error(f"Failed to load available quizzes: {e}")

        if quizzes:
            for i, quiz in enumerate(quizzes):
                quiz_id = quiz.get('quiz_id')
                if not quiz_id: continue
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{quiz.get('title', 'No Title')}**")
                    st.markdown(f"*Topic: {quiz.get('topic', 'N/A')} • Difficulty: {quiz.get('difficulty', 'N/A')}*")
                    st.markdown(f"{quiz.get('description', 'No Description')}")
                with col2:
                    if st.button("Start Quiz", key=f"start_all_quiz_{quiz_id}"):
                         if start_quiz(db, quiz_id):
                            st.rerun()
        elif not recommended_quizzes: # Only show if no quizzes are available at all
             st.info("No other quizzes available. Why not create one?")


def render_create_quiz_form(db, assistant):
    """Renders the form for creating a new quiz."""
    with st.form("create_quiz_form"):
        st.markdown("### Define Your New Quiz")
        quiz_topic = st.text_input("Quiz Topic*", help="The main subject of the quiz (e.g., 'Python Lists', 'World War II Dates').")
        quiz_title = st.text_input("Quiz Title (optional)", help="A specific title (e.g., 'Advanced Python List Comprehensions'). If blank, a title will be generated.")
        quiz_desc = st.text_area("Description (optional)", help="A brief summary of what the quiz covers.")

        col1, col2 = st.columns(2)
        with col1:
            difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1)
        with col2:
            num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5, step=1)

        submit_create = st.form_submit_button("✨ Generate Quiz ✨", use_container_width=True)

    if submit_create:
        user_id = st.session_state.get('user_id')
        if not quiz_topic:
            st.error("⚠️ Please enter a quiz topic.")
        elif not assistant:
            st.error("🚨 AI assistant is not available. Cannot create quiz.")
        elif not user_id:
             st.error("🚨 User ID not found. Cannot create quiz.")
        else:
            # Define title and description based on input or defaults
            # These are NOT passed to generate_quiz, but might be used
            # internally by the assistant or when saving results.
            title_for_display = quiz_title or f"Quiz on {quiz_topic}"
            description_for_display = quiz_desc or f"A {difficulty} level quiz about {quiz_topic}"

            with st.spinner(f"🧠 Asking the AI to create a {difficulty} quiz about '{quiz_topic}'..."):
                try:
                    # --- FIX: Call generate_quiz with ONLY the required positional arguments ---
                    quiz_id, message = assistant.generate_quiz(
                        user_id,         # Arg 1
                        quiz_topic,      # Arg 2
                        difficulty,      # Arg 3
                        num_questions    # Arg 4
                    )
                    # --------------------------------------------------------------------------

                    if quiz_id:
                        # The assistant internally handled saving the quiz with its details
                        st.success(f"✅ Quiz '{title_for_display}' created successfully! Starting now...")
                        if start_quiz(db, quiz_id): # Start the attempt
                            st.rerun()
                        else:
                            st.error("Quiz created, but failed to start the attempt.")
                    else:
                        st.error(f"⚠️ AI failed to create quiz: {message}")
                except TypeError as te:
                    # This error block specifically catches signature mismatches
                    st.error(f"🚨 Error calling AI generation: {te}")
                    st.error("Hint: The AI assistant's `generate_quiz` function was called with the wrong arguments. Please check its definition.")
                except Exception as e:
                    st.error(f"🚨 An unexpected error occurred during quiz generation: {e}")
                    # logger.exception("Quiz generation failed") # Use proper logging


def render_my_quizzes_tab(db):
    """Renders the content for the 'My Quizzes' tab."""
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.warning("User ID not found, cannot display personal quiz data.")
        return

    # Quiz statistics
    st.subheader("📈 My Statistics")
    stats = {}
    try:
        stats = db.get_quiz_stats(user_id)
        safe_stats = {
            'total_attempts': stats.get('total_attempts') or 0,
            'completed_quizzes': stats.get('completed_quizzes') or 0,
            'average_score': stats.get('average_score') or 0.0
        }
        if sum(safe_stats.values()) > 0:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Attempts", safe_stats['total_attempts'])
            col2.metric("Completed Quizzes", safe_stats['completed_quizzes'])
            avg_score_display = f"{safe_stats['average_score'] * 100:.1f}%" if safe_stats['total_attempts'] > 0 else "N/A"
            col3.metric("Average Score", avg_score_display)
        else:
             st.info("No quiz statistics available yet. Take a quiz!")
    except AttributeError:
        st.error("Database object does not support 'get_quiz_stats'.")
    except Exception as e:
        st.error(f"Failed to load quiz statistics: {e}")
    st.divider()

    # My recent quiz attempts
    st.subheader("📜 My Quiz History")
    attempts = []
    try:
       # Add limit for performance? e.g., limit=10
       attempts = db.get_user_quiz_attempts(user_id)
    except AttributeError:
        st.error("Database object does not support 'get_user_quiz_attempts'.")
    except Exception as e:
       st.error(f"Failed to load recent attempts: {e}")

    if attempts:
        # Sort attempts by timestamp if available, descending
        try:
            attempts.sort(key=lambda x: x.get('attempt_timestamp', 0), reverse=True)
        except: # Ignore sorting errors if timestamp format is inconsistent
            pass

        for i, attempt in enumerate(attempts):
            attempt_id = attempt.get('attempt_id')
            quiz_id = attempt.get('quiz_id')
            if not attempt_id or not quiz_id: continue # Skip incomplete data

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{attempt.get('title', 'No Title')}**")
                # Assuming you store timestamp (e.g., 'created_at' or similar)
                timestamp_str = str(attempt.get('attempt_timestamp', 'Unknown time'))
                if attempt.get('completed'):
                    score = attempt.get('score', 0)
                    max_score = attempt.get('max_score', 0)
                    success_rate_percent = (attempt.get('success_rate', 0) or 0) * 100
                    st.markdown(f"Status: ✅ Completed <small>({timestamp_str})</small>", unsafe_allow_html=True)
                    st.markdown(f"Score: **{score}/{max_score}** ({success_rate_percent:.1f}%)")
                else:
                    st.markdown(f"Status: ⏳ Incomplete <small>({timestamp_str})</small>", unsafe_allow_html=True)

            with col2:
                if attempt.get('completed'):
                    if st.button("View Results", key=f"view_result_{attempt_id}"):
                        st.session_state.quiz_result_id = attempt_id
                        reset_quiz_state(keep_result=True)
                        st.rerun()

            with col3:
                if not attempt.get('completed'):
                    if st.button("Continue", key=f"continue_quiz_{attempt_id}", disabled=True): # Disable for now
                        # Proper 'continue' requires loading saved state (answers, index)
                        st.warning("Continue functionality is not yet implemented.")
                        # If implemented: load_attempt_state(db, attempt_id)
                        # else: start_quiz(db, quiz_id) # Restart as fallback?
                        # st.rerun()
                    # Add a 'Retake' button?
                    if st.button("Retake", key=f"retake_quiz_{attempt_id}"):
                         if start_quiz(db, quiz_id):
                              st.rerun()

            st.markdown("---") # Separator between attempts
    else:
        st.info("You haven't taken any quizzes yet.")
    st.divider()

    # Quizzes created by me
    st.subheader("✏️ Quizzes Created By Me")
    my_quizzes = []
    try:
        my_quizzes = db.get_user_quizzes(user_id)
    except AttributeError:
        st.error("Database object does not support 'get_user_quizzes'.")
    except Exception as e:
        st.error(f"Failed to load created quizzes: {e}")

    if my_quizzes:
        # Sort? e.g., by creation date
        my_quizzes.sort(key=lambda x: x.get('created_at', 0), reverse=True)

        for i, quiz in enumerate(my_quizzes):
            quiz_id = quiz.get('quiz_id')
            if not quiz_id: continue

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{quiz.get('title', 'No Title')}**")
                st.markdown(f"*Topic: {quiz.get('topic', 'N/A')} • Difficulty: {quiz.get('difficulty', 'N/A')}*")
                st.markdown(f"{quiz.get('description', 'No Description')}")
                # Add stats? e.g., number of attempts by others, average score
            with col2:
                if st.button("Take My Quiz", key=f"take_my_quiz_{quiz_id}"):
                    if start_quiz(db, quiz_id):
                        st.rerun()
                # Add Edit/Delete buttons later?
                # if st.button("Edit", key=f"edit_my_quiz_{quiz_id}", disabled=True): pass
                # if st.button("Delete", key=f"delete_my_quiz_{quiz_id}", type="secondary", disabled=True): pass
            st.markdown("---")
    else:
        st.info("You haven't created any quizzes yet.")


# --- Core Quiz Logic Functions ---

def start_quiz(db, quiz_id):
    """Initiate a new quiz attempt. Returns True on success, False on failure."""
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("Cannot start quiz: User ID missing.")
        return False
    if not quiz_id:
         st.error("Cannot start quiz: Quiz ID missing.")
         return False

    try:
        # Always start a new attempt for now.
        attempt_id = db.start_quiz_attempt(quiz_id, user_id)
        if not attempt_id:
             st.error("Failed to create a new quiz attempt record in the database.")
             return False

        # Clear any previous state first (important!)
        reset_quiz_state(keep_result=False)

        # Initialize session state for the new attempt
        st.session_state.current_quiz_id = quiz_id
        st.session_state.current_attempt_id = attempt_id
        st.session_state.current_question_idx = 0
        st.session_state.question_start_time = time.time()
        # quiz_answers could store {question_idx: user_answer} if needed for back button/resume
        st.session_state.quiz_answers = {}

        return True

    except AttributeError:
        st.error("Database object does not support 'start_quiz_attempt'.")
        reset_quiz_state()
        return False
    except Exception as e:
        st.error(f"An error occurred while starting the quiz: {e}")
        reset_quiz_state()
        return False


def render_active_quiz(db, assistant):
    """Render the active quiz taking interface."""
    # --- State Verification ---
    required_keys = ["current_quiz_id", "current_attempt_id", "current_question_idx", "question_start_time"]
    if not all(k in st.session_state for k in required_keys):
        st.error("Quiz state is incomplete or missing. Resetting.")
        reset_quiz_state()
        st.rerun() # Rerun to show quiz selection
        return

    quiz_id = st.session_state.current_quiz_id
    attempt_id = st.session_state.current_attempt_id
    question_idx = st.session_state.current_question_idx

    try:
        # --- Fetch Data (Consider Caching these DB calls) ---
        # Fetch quiz info (title etc.)
        quiz_info = None
        try:
             quiz_info_tuple = db.get_quiz(quiz_id) # Assuming returns tuple
             if quiz_info_tuple and len(quiz_info_tuple) > 2:
                  quiz_info = {'id': quiz_info_tuple[0], 'title': quiz_info_tuple[2]} # Example mapping
             else:
                  st.error(f"Quiz info not found or incomplete (ID: {quiz_id}). Ending attempt.")
                  reset_quiz_state()
                  st.rerun()
                  return
        except AttributeError:
             st.error("DB object missing 'get_quiz'. Ending attempt.")
             reset_quiz_state(); st.rerun(); return
        except Exception as e:
            st.error(f"Error fetching quiz info: {e}. Ending attempt.")
            reset_quiz_state(); st.rerun(); return

        quiz_title = quiz_info.get('title', 'Quiz')

        # Fetch all questions for this quiz
        questions = []
        try:
             questions = db.get_quiz_questions(quiz_id) # Assuming returns list of dicts
             if not questions:
                  st.error(f"No questions found for quiz '{quiz_title}' (ID: {quiz_id}). Ending attempt.")
                  # Optionally mark attempt as errored in DB: db.mark_attempt_error(attempt_id, "no_questions")
                  reset_quiz_state()
                  st.rerun()
                  return
        except AttributeError:
             st.error("DB object missing 'get_quiz_questions'. Ending attempt.")
             reset_quiz_state(); st.rerun(); return
        except Exception as e:
             st.error(f"Error fetching questions: {e}. Ending attempt.")
             reset_quiz_state(); st.rerun(); return

        num_questions = len(questions)

        # --- Progress and Completion Check ---
        st.progress((question_idx) / num_questions, text=f"Question {question_idx + 1} / {num_questions}")
        # st.caption(f"Question {question_idx + 1} of {num_questions}") # Alternative display

        if question_idx >= num_questions:
            with st.spinner("Quiz finished! Calculating final score..."):
                try:
                    # Ensure db.complete_quiz_attempt exists and works
                    score, max_score = db.complete_quiz_attempt(attempt_id)
                    st.success("Quiz completed!")
                    st.session_state.quiz_result_id = attempt_id
                    reset_quiz_state(keep_result=True)
                    st.rerun()
                except AttributeError:
                     st.error("DB object missing 'complete_quiz_attempt'. Cannot finalize score.")
                     reset_quiz_state() # Reset fully on error
                     st.rerun()
                except Exception as e:
                    st.error(f"Error finalizing quiz results: {e}")
                    reset_quiz_state()
                    st.rerun()
            return # Stop execution after completion logic

        # --- Question Processing and Display ---
        current_question_data = questions[question_idx]
        # Add error handling inside adapt_question if needed
        adapted_question = adapt_question_if_needed(current_question_data, assistant)

        st.subheader(f"{quiz_title} - Question {question_idx + 1}")
        # Add error handling inside render_question_content if needed
        render_question_content(adapted_question)

        # --- Answer Input ---
        user_answer = get_answer_input(adapted_question, attempt_id, question_idx)

        # --- Navigation and Submission ---
        render_quiz_navigation(db, adapted_question, user_answer, attempt_id, question_idx, num_questions)

    except Exception as e:
        st.error(f"🚨 A critical error occurred during the quiz: {e}")
        # import traceback
        # st.error(traceback.format_exc()) # Show full traceback for debugging
        reset_quiz_state()
        if st.button("Go back to Quizzes"): st.rerun()
        # Consider logging the error properly
        # logger.exception(f"Critical error in render_active_quiz - attempt {attempt_id}")

# Note: adapt_question_if_needed, render_question_content, get_answer_input,
# render_quiz_navigation, submit_answer functions remain the same as in the previous version.
# Please ensure they are present in your code.

# --- Result Rendering Functions ---

def render_quiz_results(db, assistant):
    """Render the results page for a completed quiz."""
    # --- State Verification ---
    if "quiz_result_id" not in st.session_state or not st.session_state.quiz_result_id:
         st.warning("No quiz result selected to display.")
         reset_quiz_state()
         st.rerun()
         return

    attempt_id = st.session_state.quiz_result_id

    # --- Fetch Results ---
    results = None
    try:
        with st.spinner("Loading quiz results..."):
            # Ensure db.get_quiz_attempt_results exists
            results = db.get_quiz_attempt_results(attempt_id)
    except AttributeError:
         st.error("DB object missing 'get_quiz_attempt_results'. Cannot load results.")
         results = None # Ensure results is None
    except Exception as e:
        st.error(f"Failed to load results for attempt ID {attempt_id}: {e}")
        results = None # Ensure results is None

    if not results:
        st.error(f"Results data not found or failed to load for attempt ID: {attempt_id}.")
        # Provide options to user
        col1, col2 = st.columns(2)
        with col1:
             if st.button("🔄 Try Again"): st.rerun()
        with col2:
             if st.button("⬅️ Back to Quizzes"):
                reset_quiz_state()
                st.rerun()
        return # Stop execution here

    # --- Display Header and Score ---
    st.header(f"🏁 Quiz Results: {results.get('title', 'Quiz Title Missing')}")
    score = results.get('score', 0)
    max_score = results.get('max_score', 0)
    success_rate_percent = (score / max_score * 100) if max_score else 0
    st.metric("Final Score", f"{score} / {max_score}", f"{success_rate_percent:.1f}%")
    # st.subheader(f"Final Score: {score} / {max_score} ({success_rate_percent:.1f}%)") # Alternative

    # --- AI Feedback ---
    generate_and_display_ai_feedback(results, assistant)

    # --- Question Review ---
    render_question_review(results)

    # --- Navigation ---
    st.divider()
    if st.button("⬅️ Back to All Quizzes", use_container_width=True):
        reset_quiz_state(keep_result=False) # Clear the result ID now
        st.rerun()

# Note: generate_and_display_ai_feedback, render_question_review,
# render_single_question_review functions remain the same as in the previous version.
# Please ensure they are present in your code.

# --- State Management ---

def reset_quiz_state(keep_result=False):
    """Reset quiz-related session state variables safely."""
    keys_to_clear = [
        "current_quiz_id", "current_attempt_id", "current_question_idx",
        "question_start_time", "quiz_answers",
    ]
    if not keep_result:
        keys_to_clear.append("quiz_result_id")

    # print(f"Resetting state (keep_result={keep_result}). Keys: {keys_to_clear}") # Debug
    for key in keys_to_clear:
        if key in st.session_state:
            try:
                del st.session_state[key]
            except KeyError:
                 pass # Key already deleted, ignore
            except Exception as e:
                 st.warning(f"Could not delete session state key '{key}': {e}", icon="⚠️")

# --- Placeholder/Helper functions (ensure these are implemented correctly elsewhere) ---
# These functions were broken out for clarity but assumed to be the same as previous versions.
# Make sure they are included in your final file or imported correctly.

def adapt_question_if_needed(question_data, assistant):
    """Adapts the question based on user profile and assistant availability."""
    adapted_question = question_data # Default to original
    try:
        user_profile = st.session_state.get("current_profile") # Ensure profile is loaded into state
        if isinstance(user_profile, dict):
            adaptation_type = question_data.get('adaptation_type')
            disability_type = user_profile.get('disability_type', 'None')

            if assistant and (adaptation_type or disability_type != 'None'):
                try:
                    # Ensure assistant has the method and it works
                    # Use a less intrusive spinner or none?
                    # with st.spinner("Adapting question..."):
                    adapted_question = assistant.adapt_quiz_question(question_data, user_profile)
                    if 'adaptation_notes' in adapted_question and adapted_question['adaptation_notes']:
                        # Display notes subtly
                        st.caption(f"ℹ️ Adaptation Note: {adapted_question['adaptation_notes']}")
                except AttributeError:
                     st.warning("AI assistant missing 'adapt_quiz_question' method.", icon="🤖")
                except Exception as e:
                     st.warning(f"AI adaptation failed: {e}", icon="🤖")
                     adapted_question = question_data # Fallback on error
            elif (adaptation_type or disability_type != 'None') and not assistant:
                 st.caption("AI Assistant not available for question adaptation.")
        # else: # User profile not found or not dict - don't warn every time?
            # pass
    except Exception as e:
        st.error(f"Error during adaptation check: {e}")
        adapted_question = question_data # Fallback
    return adapted_question


def render_question_content(question_data):
    """Renders the text and any diagrams for a question."""
    question_text = question_data.get('question_text', '*Question text is missing.*')
    try:
        mermaid_code = extract_mermaid_code(question_text) # Assumes imported/defined
        if mermaid_code:
            question_text_no_mermaid = question_text.replace(f"```mermaid\n{mermaid_code}\n```", "").strip()
            st.markdown(question_text_no_mermaid)
            render_mermaid(mermaid_code) # Assumes imported/defined
        else:
            st.markdown(question_text)
    except NameError as ne:
         st.error(f"Rendering function missing: {ne}. Cannot render diagrams.")
         st.markdown(question_text) # Show text anyway
    except Exception as e:
         st.error(f"Error rendering question content: {e}")
         st.markdown(question_text) # Fallback


def get_answer_input(question_data, attempt_id, question_idx):
    """Gets the user's answer input based on question type."""
    user_answer = None
    question_type = question_data.get('question_type', '').lower()
    options = question_data.get('options', [])
    input_key = f"q_{attempt_id}_{question_idx}" # Unique key per question instance

    # Use st.container to group label and input for better layout/styling if needed
    # with st.container(border=True):
    if question_type == "multiple choice":
        if isinstance(options, list) and options:
            # Add a label above the radio options
            st.markdown("**Select the best answer:**")
            user_answer = st.radio("Select the best answer:", options, key=input_key, index=None, label_visibility="collapsed")
        else:
            st.error("Invalid/missing options for Multiple Choice.")
            st.stop() # Prevent continuation if question is broken
    elif question_type == "true/false":
        st.markdown("**Select True or False:**")
        user_answer = st.radio("Select True or False:", ["True", "False"], key=input_key, index=None, label_visibility="collapsed")
    elif question_type == "short answer":
        st.markdown("**Enter your answer below:**")
        user_answer = st.text_input("Your answer:", key=input_key, label_visibility="collapsed", placeholder="Type your short answer here...")
    else:
        st.error(f"Unsupported question type encountered: '{question_data.get('question_type')}'")
        st.stop() # Stop if type is unknown
    return user_answer


def render_quiz_navigation(db, question_data, user_answer, attempt_id, question_idx, num_questions):
    """Renders the Next/Finish and Quit buttons."""
    # Use columns for button layout
    col_quit, col_spacer, col_next = st.columns([1, 2, 1]) # Adjust ratios as needed

    with col_quit:
         # Make quit less prominent?
         if st.button("Quit", type="secondary", use_container_width=True):
            # Consider adding st.confirm for safety
            # if st.confirm("Are you sure you want to quit this attempt?"):
            reset_quiz_state()
            st.rerun()

    with col_next:
        disable_next = False
        question_type = question_data.get('question_type', '').lower()
        if (question_type in ["multiple choice", "true/false"]) and user_answer is None:
             disable_next = True
        elif question_type == "short answer" and not (user_answer and user_answer.strip()): # Check if string is not empty/whitespace
             disable_next = True

        is_last_question = (question_idx >= num_questions - 1)
        button_label = "Finish Quiz 🏁" if is_last_question else "Next Question ➡️"

        if st.button(button_label, disabled=disable_next, type="primary", use_container_width=True):
            # Perform answer submission logic
            if submit_answer(db, question_data, user_answer, attempt_id): # Check if submission succeeded
                # Move to next question or finish
                st.session_state.current_question_idx += 1
                st.session_state.question_start_time = time.time() # Reset timer
                st.rerun()
            # else: Error handled within submit_answer by stopping execution


def submit_answer(db, question_data, user_answer, attempt_id):
    """Calculates correctness and records the response. Returns True on success, False on failure."""
    try:
        time_spent = int(time.time() - st.session_state.question_start_time)
        correct_answer = question_data.get('correct_answer')
        is_correct = False
        question_id = question_data.get('question_id')

        if not question_id:
             st.error("Internal Error: Question ID missing. Cannot save answer.")
             return False

        if correct_answer is not None:
            user_ans_str = str(user_answer or "").strip().lower()
            correct_ans_str = str(correct_answer).strip().lower()
            is_correct = user_ans_str == correct_ans_str
        else:
             st.caption("Warning: Correct answer data missing; unable to grade.", unsafe_allow_html=True)

        # Ensure db.record_question_response exists
        db.record_question_response(
            attempt_id,
            question_id,
            user_answer if user_answer is not None else "",
            is_correct,
            time_spent
        )
        return True # Indicate success
    except AttributeError:
         st.error("DB object missing 'record_question_response'. Cannot save answer.")
         return False
    except Exception as e:
        st.error(f"Failed to save your answer: {e}")
        return False # Indicate failure


def generate_and_display_ai_feedback(results, assistant):
    """Generates and displays AI feedback if possible."""
    if not assistant: return # Skip if no assistant

    user_profile = st.session_state.get("current_profile") # Assumes profile is loaded
    if not isinstance(user_profile, dict):
        st.caption("User profile not available for personalized feedback.")
        return

    with st.spinner("💡 Generating personalized feedback..."):
        try:
            # Ensure assistant.generate_quiz_feedback exists
            feedback = assistant.generate_quiz_feedback(results, user_profile)
            if feedback: # Check if feedback is not empty
                 st.info(f"**AI Feedback:**\n\n{feedback}")
            # else: No feedback generated, don't show anything
        except AttributeError:
             st.warning("AI Assistant object missing 'generate_quiz_feedback' method.", icon="🤖")
        except Exception as e:
            st.warning(f"Could not generate AI feedback: {e}", icon="🤖")


def render_question_review(results):
    """Displays the detailed review of each question."""
    st.subheader("🔍 Question Review")
    questions_data = results.get('questions', [])
    if not questions_data:
        st.warning("No detailed question review available for this attempt.")
        return

    for i, q_result in enumerate(questions_data):
        is_correct = q_result.get('is_correct')
        icon = "✅" if is_correct is True else "❌" if is_correct is False else "❔"
        expander_label = f"{icon} Question {i+1}"
        expander_label += " (Correct)" if is_correct is True else " (Incorrect)" if is_correct is False else " (Not Graded)"

        with st.expander(expander_label, expanded=False):
            render_single_question_review(q_result)


def render_single_question_review(q_result):
    """Renders the details for a single question in the review."""
    question_text = q_result.get('question_text', '*Question text missing*')
    options = q_result.get('options') # List for MC, None otherwise?
    user_answer = q_result.get('user_answer', '*No answer recorded*')
    correct_answer = q_result.get('correct_answer', '*Correct answer missing*')
    explanation = q_result.get('explanation')
    is_correct = q_result.get('is_correct')

    # Render question text (and potential Mermaid)
    st.markdown("**Question:**")
    render_question_content(q_result) # Re-use the function
    st.markdown("---")

    # Display options or answers based on question type (implicitly)
    st.markdown("**Answer & Explanation:**")
    if options and isinstance(options, list): # MC Type Display
        for option in options:
            prefix = "➖ " # Default prefix
            option_str = str(option)
            correct_ans_str = str(correct_answer)
            user_ans_str = str(user_answer)
            suffix = ""

            is_this_correct_ans = (option_str == correct_ans_str)
            is_this_user_ans = (option_str == user_ans_str)

            if is_this_correct_ans:
                prefix = "✅ "
                suffix = " *(Correct Answer)*"
            if is_this_user_ans:
                 if is_correct:
                      # User picked the correct answer
                      suffix += " *(Your Choice)*"
                 else:
                      # User picked an incorrect answer
                      prefix = "❌ "
                      suffix += " *(Your Choice)*"

            st.markdown(f"{prefix} {option}{suffix}")

    else: # Non-MC Type Display (True/False, Short Answer)
         # Display user answer with status icon
         status_icon = "✅" if is_correct else "❌" if is_correct is False else "❔"
         st.markdown(f"Your answer: {status_icon} `{user_answer}`")
         # Only show correct answer if incorrect or not graded
         if is_correct is False or correct_answer is None:
             st.markdown(f"Correct answer: `{correct_answer}`")

    # Show Explanation if available
    if explanation and explanation.strip():
        st.markdown("**Explanation:**")
        st.markdown(f"> {explanation}") # Blockquote formatting
    # else: st.caption("No explanation provided for this question.")