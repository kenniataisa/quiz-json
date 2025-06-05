import streamlit as st
import json

st.set_page_config(page_title="Quiz App", page_icon="❓")

def parse_special_json(data):
    raw_text = ""
    for item in data:
        for _, value in item.items():
            raw_text += value

    try:
        questions = []
        json_text = raw_text.replace("[", "").replace("]", "")
        json_blocks = json_text.split("}{")

        for i, block in enumerate(json_blocks):
            if i == 0:
                block = block + "}"
            elif i == len(json_blocks) - 1:
                block = "{" + block
            else:
                block = "{" + block + "}"

            try:
                q_data = json.loads(block)
                if "pergunta" in q_data and "resposta_correta" in q_data:
                    questions.append(q_data)
            except json.JSONDecodeError:
                pass

        return questions
    except Exception as e:
        st.error(f"Erro ao processar o JSON especial: {str(e)}")
        return None

def load_questions(uploaded_file):
    try:
        data = json.load(uploaded_file)

        if isinstance(data, list) and len(data) > 0 and any("[" in item for item in data[0]):
            questions = parse_special_json(data)
            if questions and len(questions) > 0:
                return questions

        if isinstance(data, list):
            valid_questions = []
            for q in data:
                if isinstance(q, dict) and "pergunta" in q and "resposta_correta" in q:
                    tipo = q.get("tipo", "multipla_escolha")

                    if tipo == "verdadeiro_falso":
                        if "opcoes" not in q:
                            q["opcoes"] = ["Verdadeiro", "Falso"]
                        if isinstance(q["resposta_correta"], int):
                            try:
                                q["resposta_correta"] = q["opcoes"][q["resposta_correta"]]
                            except IndexError:
                                continue
                        valid_questions.append(q)

                    elif tipo == "multipla_escolha":
                        if "opcoes" in q and isinstance(q["opcoes"], list) and len(q["opcoes"]) > 0:
                            valid_questions.append(q)

            return valid_questions if valid_questions else None
        else:
            return None
    except json.JSONDecodeError:
        st.error("Arquivo JSON inválido.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar questões: {str(e)}")
        return None

def initialize_session_state(questions):
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "questions" not in st.session_state:
        st.session_state.questions = questions
    for i in range(len(questions)):
        if f"answer_{i}" not in st.session_state:
            st.session_state[f"answer_{i}"] = None
            st.session_state[f"answered_{i}"] = False

def show_question_feedback(question, index):
    user_answer = st.session_state[f"answer_{index}"]
    is_true_false = question.get("tipo") == "verdadeiro_falso"
    is_correct = user_answer == question["resposta_correta"]

    if is_true_false:
        if is_correct:
            st.success(f"✅ Correto! A resposta é: {question['resposta_correta']}")
        else:
            st.error(f"❌ Incorreto. A resposta correta é: {question['resposta_correta']}")
    else:
        correct_option = question["opcoes"][question["resposta_correta"]]
        cols = st.columns(2)
        for i, option in enumerate(question["opcoes"]):
            with cols[i % 2]:
                if i == question["resposta_correta"]:
                    st.markdown(f"""<div style="background-color: #4CAF50; color: white; border-radius: 0.5rem;
                    padding: 0.5rem 1rem; margin: 0.25rem 0; text-align: center;">{option} ✓</div>""", unsafe_allow_html=True)
                elif i == user_answer and not is_correct:
                    st.markdown(f"""<div style="background-color: #F44336; color: white; border-radius: 0.5rem;
                    padding: 0.5rem 1rem; margin: 0.25rem 0; text-align: center;">{option} ❌</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="background-color: #E0E0E0; color: black; border-radius: 0.5rem;
                    padding: 0.5rem 1rem; margin: 0.25rem 0; text-align: center;">{option}</div>""", unsafe_allow_html=True)

        if is_correct:
            st.success("✅ Correto!")
        else:
            st.error(f"❌ Incorreto. Resposta correta: {correct_option}")

    if "explicacao" in question:
        st.info(f"Explicação: {question['explicacao']}")

def show_question_options(question, index):
    is_true_false = question.get("tipo") == "verdadeiro_falso"
    options = question.get("opcoes", [])

    if is_true_false:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verdadeiro", key=f"button_{index}_true", use_container_width=True):
                st.session_state[f"answer_{index}"] = "Verdadeiro"
                st.session_state[f"answered_{index}"] = True
                st.rerun()
        with col2:
            if st.button("Falso", key=f"button_{index}_false", use_container_width=True):
                st.session_state[f"answer_{index}"] = "Falso"
                st.session_state[f"answered_{index}"] = True
                st.rerun()
    else:
        cols = st.columns(2)
        for i, option in enumerate(options):
            with cols[i % 2]:
                if st.button(option, key=f"button_{index}_{i}", use_container_width=True):
                    st.session_state[f"answer_{index}"] = i
                    st.session_state[f"answered_{index}"] = True
                    st.rerun()

def display_question(question, index):
    if not isinstance(question, dict) or "pergunta" not in question:
        st.error(f"Questão {index + 1} com formato inválido.")
        return

    tipo = question.get("tipo", "multipla_escolha")
    badge = "✅❌ Verdadeiro/Falso" if tipo == "verdadeiro_falso" else "🔘 Múltipla Escolha"

    st.subheader(f"Questão {index + 1}: {question['pergunta']}")
    st.caption(badge)

    if st.session_state[f"answered_{index}"]:
        show_question_feedback(question, index)
    else:
        show_question_options(question, index)

def show_progress():
    total = len(st.session_state.questions)
    answered = sum(1 for i in range(total) if st.session_state[f"answered_{i}"])
    st.progress(answered / total)
    st.caption(f"Progresso: {answered}/{total} respondidas")

def show_navigation_controls():
    total = len(st.session_state.questions)
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("⏮ Anterior", use_container_width=True) and st.session_state.current_question > 0:
            st.session_state.current_question -= 1
            st.rerun()

    with col2:
        st.write(f"Questão {st.session_state.current_question + 1}/{total}")

    with col3:
        if st.button("Próxima ⏭", use_container_width=True) and st.session_state.current_question < total - 1:
            st.session_state.current_question += 1
            st.rerun()

def show_final_score():
    total = len(st.session_state.questions)
    correct = 0

    for i in range(total):
        question = st.session_state.questions[i]
        user_answer = st.session_state[f"answer_{i}"]
        if question.get("tipo") == "verdadeiro_falso":
            if user_answer == question["resposta_correta"]:
                correct += 1
        else:
            if user_answer == question["resposta_correta"]:
                correct += 1

    st.success(f"🎉 Você concluiu! Pontuação: {correct}/{total} ({correct/total:.0%})")
    st.balloons()

def main():
    st.title("📝 Quiz Interativo")

    uploaded_file = st.file_uploader("Faça upload do arquivo de questões (JSON)", type="json")

    if uploaded_file is not None:
        questions = load_questions(uploaded_file)

        if questions:
            st.sidebar.write("📊 Total de questões:", len(questions))
            st.sidebar.write("✅❌ Verdadeiro/Falso:", sum(1 for q in questions if q.get("tipo") == "verdadeiro_falso"))
            st.sidebar.write("🔘 Múltipla Escolha:", sum(1 for q in questions if q.get("tipo") == "multipla_escolha"))

            initialize_session_state(questions)
            show_progress()
            show_navigation_controls()

            current = st.session_state.current_question
            if 0 <= current < len(questions):
                display_question(questions[current], current)
            else:
                st.error("Índice da questão fora do intervalo")

            if all(st.session_state[f"answered_{i}"] for i in range(len(questions))):
                show_final_score()
        else:
            st.error("Não foi possível carregar perguntas válidas.")

if __name__ == "__main__":
    main()
