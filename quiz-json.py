import streamlit as st
import json

# Page configuration
st.set_page_config(page_title="Quiz App", page_icon="❓")

def parse_special_json(data):
    """Parse the special JSON format from slide1.json"""
    raw_text = ""
    for item in data:
        for key, value in item.items():
            # Add each value to the raw text
            raw_text += value
    
    try:
        # Try to parse the reconstructed JSON text
        questions = []
        json_text = raw_text.replace("[", "").replace("]", "")
        json_blocks = json_text.split("}{")
        
        for i, block in enumerate(json_blocks):
            # Fix the JSON blocks
            if i == 0:
                block = block + "}"
            elif i == len(json_blocks) - 1:
                block = "{" + block
            else:
                block = "{" + block + "}"
                
            try:
                q_data = json.loads(block)
                if "pergunta" in q_data and "opcoes" in q_data and "resposta_correta" in q_data:
                    questions.append(q_data)
            except json.JSONDecodeError:
                pass
                
        return questions
    except Exception as e:
        st.error(f"Error parsing special JSON format: {str(e)}")
        return None

def load_questions(uploaded_file):
    """Load questions from a JSON file with error handling"""
    try:
        # First try normal JSON loading
        data = json.load(uploaded_file)
        
        # If the data looks like our special format
        if isinstance(data, list) and len(data) > 0 and any("[" in item for item in data[0]):
            questions = parse_special_json(data)
            if questions and len(questions) > 0:
                return questions
        
        # Otherwise process as normal JSON
        if isinstance(data, list):
            # Validate each question has the required fields
            valid_questions = []
            for q in data:
                if isinstance(q, dict) and "pergunta" in q and "opcoes" in q and "resposta_correta" in q:
                    valid_questions.append(q)
            
            if valid_questions:
                return valid_questions
            else:
                st.error("No valid questions found in the JSON file")
                return None
        else:
            st.error("Invalid format: The JSON should contain an array of questions")
            return None
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please upload a valid JSON file.")
        return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def initialize_session_state(questions):
    """Initialize all required session state variables"""
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    
    if "questions" not in st.session_state:
        st.session_state.questions = questions
    
    # Initialize answer tracking for all questions
    for i in range(len(questions)):
        if f"answer_{i}" not in st.session_state:
            st.session_state[f"answer_{i}"] = None
            st.session_state[f"answered_{i}"] = False

def show_question_feedback(question, index):
    """Display feedback after a question is answered"""
    user_answer = st.session_state[f"answer_{index}"]
    is_correct = user_answer == question["resposta_correta"]
    
    # Show all options with color feedback
    cols = st.columns(2)
    for i, option in enumerate(question["opcoes"]):
        with cols[i % 2]:
            # Apply CSS styling directly through markdown
            if i == question["resposta_correta"]:
                st.markdown(f"""
                <div style="background-color: #4CAF50; color: white; border-radius: 0.5rem; 
                padding: 0.5rem 1rem; margin: 0.25rem 0; text-align: center;">
                {option} ✓
                </div>
                """, unsafe_allow_html=True)
            elif i == user_answer and not is_correct:
                st.markdown(f"""
                <div style="background-color: #F44336; color: white; border-radius: 0.5rem; 
                padding: 0.5rem 1rem; margin: 0.25rem 0; text-align: center;">
                {option} ❌
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #E0E0E0; color: black; border-radius: 0.5rem; 
                padding: 0.5rem 1rem; margin: 0.25rem 0; text-align: center;">
                {option}
                </div>
                """, unsafe_allow_html=True)
    
    # Show additional feedback
    if is_correct:
        st.success("✅ Correct answer!")
    else:
        st.error(f"❌ Incorrect. The correct answer is: {question['opcoes'][question['resposta_correta']]}")
    
    if "explicacao" in question:
        st.info(f"Explanation: {question['explicacao']}")

def show_question_options(question, index):
    """Display interactive question options"""
    cols = st.columns(2)
    options = question.get("opcoes", [])
    for i, option in enumerate(options):
        with cols[i % 2]:
            if st.button(option, key=f"button_{index}_{i}"):
                st.session_state[f"answer_{index}"] = i
                st.session_state[f"answered_{index}"] = True
                st.rerun()

def display_question(question, index):
    """Display a single question with its options"""
    if not isinstance(question, dict) or "pergunta" not in question:
        st.error(f"Invalid question format for question {index + 1}")
        return
    
    st.subheader(f"Question {index + 1}: {question['pergunta']}")
    
    # Initialize question state if not exists
    if f"answer_{index}" not in st.session_state:
        st.session_state[f"answer_{index}"] = None
        st.session_state[f"answered_{index}"] = False
    
    # Show either feedback or interactive options
    if st.session_state[f"answered_{index}"]:
        show_question_feedback(question, index)
    else:
        show_question_options(question, index)

def show_progress():
    """Display quiz progress bar"""
    total = len(st.session_state.questions)
    answered = sum(1 for i in range(total) if st.session_state[f"answered_{i}"])
    st.progress(answered / total)
    st.caption(f"Progress: {answered}/{total} questions answered")

def show_navigation_controls():
    """Display question navigation controls"""
    total = len(st.session_state.questions)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⏮ Previous") and st.session_state.current_question > 0:
            st.session_state.current_question -= 1
            st.rerun()
    
    with col2:
        st.write(f"Question {st.session_state.current_question + 1}/{total}")
    
    with col3:
        if st.button("Next ⏭") and st.session_state.current_question < total - 1:
            st.session_state.current_question += 1
            st.rerun()

def show_final_score():
    """Display final score when all questions are answered"""
    total = len(st.session_state.questions)
    correct = sum(
        1 for i in range(total)
        if st.session_state[f"answer_{i}"] == st.session_state.questions[i]["resposta_correta"]
    )
    st.success(f"🎉 Quiz completed! Score: {correct}/{total} ({correct/total:.0%})")

def main():
    st.title("📝 Quiz Application")
    
    uploaded_file = st.file_uploader("Upload your quiz questions (JSON)", type="json")
    
    if uploaded_file is not None:
        questions = load_questions(uploaded_file)
        
        if questions and len(questions) > 0:
            initialize_session_state(questions)
            show_progress()
            show_navigation_controls()
            
            current_idx = st.session_state.current_question
            if 0 <= current_idx < len(st.session_state.questions):
                display_question(st.session_state.questions[current_idx], current_idx)
            else:
                st.error("Question index out of range")
            
            # Show final score if all questions answered
            total = len(st.session_state.questions)
            if all(st.session_state[f"answered_{i}"] for i in range(total)):
                show_final_score()
        else:
            st.error("Could not load valid questions from the file")

# Optional: Add a way to use the slide1.json data directly
def use_sample_questions():
    """Use a predefined set of questions for demonstration"""
    st.write("Using sample questions...")
    # Add your sample JSON handling here

if __name__ == "__main__":
    main()