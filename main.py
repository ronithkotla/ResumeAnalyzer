import time
import streamlit as st
from pdfminer.high_level import extract_text
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.exceptions import OutputParserException

# Set your Groq API key directly
GROQ_API_KEY = "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"

# Define the chatbot class
class GroqChatbot:
    def __init__(self):
        self.llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="llama-3.1-70b-versatile")

    def get_response(self, user_input):
        # Append the user's input to the conversation history
        st.session_state.conversation_history.append({"role": "user", "content": user_input})

        # Prepare the conversation history for the prompt
        prompt_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversation_history[-5:]])  # Use the last 5 exchanges

        # Create a prompt for the chatbot
        prompt = PromptTemplate.from_template(
            f"""
            ### CONVERSATION HISTORY:
            {prompt_text}

            ### INSTRUCTION:
            Respond as a professional career guidance chatbot. Provide basic suggestions based on conversation history and provide advice and suggestions on the resume given,feedback,resume score. 
            Do not provide any help or advice that is not a part of career related feild; and ask the user if they need any advice or suggestion related to career guidance.
            """
        )
        
        # Retry mechanism for handling rate limits
        retries = 3
        for attempt in range(retries):
            try:
                response = prompt | self.llm
                result = response.invoke(input={})
                bot_response = result.content.strip()

                # Append the bot's response to the conversation history
                st.session_state.conversation_history.append({"role": "Interviewer", "content": bot_response})
                return bot_response
            except OutputParserException as e:
                return f"Error: {str(e)}"
            except Exception as e:
                if 'Rate limit reached' in str(e):
                    wait_time = 60  # Wait for 60 seconds before retrying
                    st.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return f"Error: {str(e)}"

# Streamlit UI setup
def main():
    st.title("Groq Interviewer Chatbot")
    st.write("Chat with the Groq-powered interviewer chatbot!")

    # Initialize session state variables if they do not exist
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    if 'pdf_processed' not in st.session_state:
        st.session_state.pdf_processed = False

    # PDF file uploader
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file is not None and not st.session_state.pdf_processed:
        extracted_text = extract_text(uploaded_file)
        # Initialize the conversation history with extracted PDF text as user input
        # st.session_state.conversation_history.append({"role": "user", "content": extracted_text})
        st.session_state.pdf_processed = True

        # After processing the PDF, prompt the chatbot to start asking questions
        chatbot = GroqChatbot()
    
        initial_question = chatbot.get_response(extracted_text)  # Get the first question based on PDF content
        # st.session_state.conversation_history.append({"role": "Interviewer", "content": initial_question})

    # Display conversation history with styled boxes
    if st.session_state.conversation_history:
        for msg in st.session_state.conversation_history:
            if msg['role'] == 'user':
                st.markdown(
                    f"""
                    <div style='text-align: right; background-color: #414A4C; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                        <strong>You:</strong> {msg['content']}
                    </div>
                    """, unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style='text-align: left; background-color: #000000; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                        <strong>Interviewer:</strong> {msg['content']}
                    </div>
                    """, unsafe_allow_html=True
                )

    # Input area for user responses with immediate updates to session state
    st.text_input("Your Response:", key="user_input", on_change=send_message)

def send_message():
    if st.session_state.user_input:
        # Initialize the chatbot instance
        chatbot = GroqChatbot()
        # Get response from the chatbot with the latest user input
        bot_response = chatbot.get_response(st.session_state.user_input)
        # Append the bot's response to the conversation history
        # st.session_state.conversation_history.append({"role": "Interviewer", "content": bot_response})
        # Clear the input for the next question
        st.session_state.user_input = ""

if __name__ == "__main__":
    main()
