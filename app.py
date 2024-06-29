from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from handlers.commands import CommandHandler
import time

# Prepare the instance of the Flask Application.
app = Flask(__name__)
command_handler = CommandHandler()

# Dictionary to store conversation histories
conversations = {}

SESSION_EXPIRATION_TIME = 10 * 60

def update_conversation(user_id, message):
    current_time = time.time()
    if user_id in conversations:
        conversations[user_id]['history'].append(message)
        conversations[user_id]['last_active'] = current_time
    else:
        conversations[user_id] = {
            'history': [message],
            'last_active': current_time
        }

def get_conversation_history(user_id):
    if user_id in conversations:
        return "\n".join(conversations[user_id]['history'])
    return ""

def clear_expired_sessions():
    current_time = time.time()
    expired_users = [user_id for user_id, session in conversations.items()
                     if current_time - session['last_active'] > SESSION_EXPIRATION_TIME]
    for user_id in expired_users:
        del conversations[user_id]

@app.route('/bot', methods=['POST'])
def bot():
    
    """
    Handles incoming messages via a POST request to the '/bot' route.
    Extracts the first word of the incoming message to use as a command keyword
    and dispatches the command to the CommandHandler for processing.
    
    Parameters:
        None, but expects a POST request containing a 'Body' field with the incoming message.

    Returns:
        A TwiML response with the command processing result to be sent back to the sender.
    """
    
    try:
        # Clear expired sessions
        clear_expired_sessions()

        # Get the user's phone number to identify the session
        user_id = request.values.get('From', '')

        # Get the whole message that is send by the user.
        incoming_msg = request.values.get('Body', '')

        # Update the conversation history
        update_conversation(user_id, f"User: {incoming_msg}")

        # Extract the first word.
        first_word = str(incoming_msg.split()[0]).lower()
        #hard coded gemini
        first_word = "gemini"

        #bot identity hardcoded
        bot_identity = "Your name is Dzvambu a chatbot designed by ABC Bank, a bot for ABC Bank. ABC Bank has branches in Zimbabwe in every city. Your job is to assist clients. You are to reply 'Sorry I do not get your question you can chat with one of our agents, here at this number +263777000000' if the below question is not related to the bank question. "
        bot_identity += "If they greet you on their last message, you introduce yourself and tell them about the bank services. You are to answer the client if their question has something to do with banking services. Under any circumstances you are not to tell the client that you are gemini. "
        bot_identity += "If client uses another language, you translate to their language and then respond in their language, If you fail to translate you respond 'Sorry I can only understand English for the momemnt'"
        bot_identity += "Now respond to the below below\n\n"

        # Get the conversation history
        conversation_history = get_conversation_history(user_id)

        # Message of the user.
        message = ' '.join(incoming_msg.split()[1:])

        # Combine the bot identity, conversation history, and the new message
        combined_message = f"{bot_identity}{conversation_history}\nUser: {message}\n"

        # Get the response.
        response = command_handler.handle_command(first_word, bot_identity+combined_message)

        # Update the conversation history with the bot's response
        update_conversation(user_id, f"Nyasha: {response}")


        # Prepare & return the response back to WhatsApp.
        resp = MessagingResponse()
        msg = resp.message()
        msg.body(response)
        return str(resp)

    # Handle any errors.
    except Exception as e:
        print(f"An error occurred while processing the request: {e}")
        return str(MessagingResponse().message("Sorry, an error occurred while processing your request."))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')