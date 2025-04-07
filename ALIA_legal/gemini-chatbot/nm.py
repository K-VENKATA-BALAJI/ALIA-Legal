import os
import google.generativeai as genai

genai.configure(api_key="AIzaSyBa8VOem7ZMSZ46LguSkSfdYbUy-4hr7Tw")

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash",
  generation_config=generation_config,
)
history=[]

while True:
    ui=input("ask:")
    chat_session = model.start_chat(history=history)

    response = chat_session.send_message(ui)
    mr =response.text

    print(f'bot:{mr}')
    print()
    history.append( { "role":"user","parts":[ui]})
    history.append( { "role":"model","parts":[mr]})