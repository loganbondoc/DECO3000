import requests
import json
import streamlit as st
import os
from exa_py import Exa
from dotenv import load_dotenv

load_dotenv()
wordware_api_key = os.getenv('WORDWARE_API_KEY')
exa_api_key = os.getenv("EXA_API_KEY")
# Initialize session state for output
if 'output_text' not in st.session_state:
    st.session_state['output_text'] = "Start"


def remove_backticks(input_string):
    return input_string.replace('`', '')


def do_search(search_query):
    exa = Exa(api_key=exa_api_key)
    result = exa.search_and_contents(
        search_query,
        type="neural",
        use_autoprompt=True,
        num_results=5,
        text=True,
        category="research paper",
        highlights=True,
        summary=True
    )
    print("Result from search:", result)
    return result


def do_wordware(prompt_id, inputs_wordware, api_key):
    response = requests.post(
        f"https://app.wordware.ai/api/released-app/{prompt_id}/run",
        json={"inputs": inputs_wordware},
        headers={"Authorization": f"Bearer {api_key}"},
        stream=True,
    )
    if response.status_code != 200:
        st.error(f"Request failed with status code {response.status_code}.")
    else:
        # Successful api call
        text_output = ""
        for line in response.iter_lines():
            if line:
                content = json.loads(line.decode("utf-8"))
                value = content["value"]
                # We can print values as they're generated
                if value["type"] == "generation":
                    if value["state"] == "start":
                        print("\nNEW GENERATION -", value["label"])
                    else:
                        print("\nEND GENERATION -", value["label"])
                elif value["type"] == "chunk":
                    # print(value["value"], end="")
                    text_output += value["value"]
                elif value["type"] == "outputs":
                    # Or we can read from the outputs at the end
                    # Currently we include everything by ID and by label - this will likely change in future in a breaking
                    # change but with ample warning
                    print("\nFINAL OUTPUTS:")
                    # print(json.dumps(value, indent=4))
        st.session_state['output_text'] = text_output + st.session_state['output_text']
        print("Text output", text_output)
        return text_output


st.header("Welcome to essay cheater bot:")

question_chosen = st.text_input(
    "What essay question have you chosen?"
)
# Use streamlit to give us a text input for a description of the product
essay_point = st.text_input(
    "Describe your point you want to drive for this essay:"
)

transcript = "Start"
if essay_point:
    thought = ""
    action = ""
    # word_count + mark
    # Initial system instructions:
    system_instructions = """
        You are an agent that specialises in creating academic persuasive essays. You as an agent have additional tools in your arsenal. You are NOT to ask users to complete this task themselves. You are also to ensure that the quality of the output is top level otherwise you are to refine the output. In addition you are to ensure that the essay is between 900-1100 words a counter will be provided to you. Keep note of a structure of an essay and the general process of creating an essay from scratch. It needs to be academic AND highly persuasive. If you feel the essay is done you can use the done action to finish the loop.
        Here are the tools you have available to you:
        1. research
        2. summarise
        3. essay_writer
        4. done
        In your outputs you are to use the following format:
        Question: the input question you must answer
        Thought: you should always think about what to do in one sentence
        Action: the action to take, should be exaSearch, summarise, mark, word_count or done
        Input: the input to the action
        Observation: the result of the action
    """
    # if st.button("test"):
    #     inputs = {
    #         "thought": "I need to start by researching the topic of symbol grounding and the problem of representation in AI, focusing on arguments that data is not good enough for effective AI representation",
    #     }
    #     st.write("Inputs:", inputs)
    #     action = do_wordware("2ad6d7ed-4969-4e75-b725-49a4634058a2", inputs, wordware_api_key)
    #     print(action)
    #     st.write(action)

    if st.button("start analysing"):
        while action != "done":
            inputs = {
                "system_instructions": system_instructions,
                "question_chosen": question_chosen,
                "essay_point": essay_point,
                "transcript": transcript
            }
            # st.write(inputs)
            st.write("Thought inputs: ", inputs)
            thought = do_wordware("9cd71fbb-7ded-49d6-8310-58051ac02b17", inputs, wordware_api_key)
            transcript = transcript + str(thought)
            st.write("Thought:", thought)
            if thought != "":
                inputs = {
                    "thought": thought,
                }
                # st.write("Inputs:", inputs)
                action = do_wordware("2ad6d7ed-4969-4e75-b725-49a4634058a2", inputs, wordware_api_key)
                transcript = transcript + action
                action = remove_backticks(action)
                st.write("Action:", action)
                # Lets do a check on the action
                if action == "research":
                    research_inputs = {
                        "transcript": transcript,
                        "thought": thought
                    }
                    # st.write("Search term inputs", research_inputs)
                    search_term = do_wordware("b7576e08-9e07-4f18-bb89-0ee0661eabf9", research_inputs, wordware_api_key)
                    transcript = transcript + search_term
                    st.write("Search term:", search_term)
                    research = do_search(search_term)
                    st.session_state["output_text"] = st.session_state["output_text"] + str(research)
                    transcript = transcript + str(research)

                    st.write("Research", research)
                elif action == "summarise":
                    summary_input = {
                        "transcript": transcript
                    }
                    summary = do_wordware("0a809bda-a4ed-40dd-a88d-d208a607546c", summary_input, wordware_api_key)
                    st.session_state["output_text"] = summary
                    # Here we want to overwrite with summary
                    transcript = summary
                    st.write("Summary:", summary)
                elif action == "mark":
                    print("Mark")
                elif action == "essay_writer":
                    essay_input = {
                        "transcript": transcript,
                        "essay_question": question_chosen,
                        "essay_point": essay_point
                    }
                    st.write("Essay input", essay_input)
                    essay = do_wordware("9dfa55a3-1880-4cdc-9569-2f9b791fa2f6", essay_input, wordware_api_key)
                    st.write("Essay:", essay)
                    st.session_state["output_text"] = st.session_state["output_text"] + "Essay: " + essay
                    transcript = transcript + essay
                elif action == "done":
                    st.write("Done!")
                    break

st.write(st.session_state['output_text'])