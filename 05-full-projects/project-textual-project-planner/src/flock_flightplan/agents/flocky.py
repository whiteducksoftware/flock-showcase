
from datetime import datetime
import uuid
from flock.core import Flock, FlockFactory, flock_type
from pydantic import BaseModel, Field

@flock_type
class Message(BaseModel):
    content: str = Field(description="The content of the message")
    role: str = Field(description="The role of the message")
    timestamp: str = Field(default= datetime.now().strftime("%Y-%m-%d %H:%M:%S"), description="The timestamp of the message")
    id: str = Field(default=uuid.uuid4, description="The id of the message")
    context: str = Field(default="", description="The context of the message")


message_history : list[Message] = []
message_history.append(Message(content="Hello, I'm Flocky! How can I help you today? Please enter your command or message below.", role="flocky"))

async def generate_flocky_response(user_input: str, context: str)->str:
    flock = Flock(model="gpt-4.1-2025-04-14")

    flocky = FlockFactory.create_default_agent(
        name="flocky",
        description="A helpful assistant that formulates answers based on the user's input and the project plan." 
        "Project plan contains the project plan for the user. Your job is to explain the project plan to the user.",
        input="user_input: str, project_plan: str, previous_messages: list[Message]",
        output="answer: str | answer to the user's input with information from the project plan",
        write_to_file=True,
        no_output=True,
    )
    
    flock.add_agent(flocky)

    result = await flock.run_async(
        start_agent="flocky",
        input={
            "user_input": user_input,
            "project_plan": context,
            "previous_messages": message_history,
        },
    )
    answer = result.answer

    message_history.append(Message(content=user_input, role="user"))
    message_history.append(Message(content=answer, role="flocky"))

    return result
