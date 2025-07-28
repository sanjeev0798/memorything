import streamlit as st
import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Constants
STL_FOLDER = "stl"
CUSTOM_SUGGESTIONS_FILE = "custom_suggestions.txt"
SUGGESTIONS_JSON = "suggestion_to_stl.json"
GENERIC_WORDS = {"keychain", "charm", "pendant", "token", "object", "mini", "symbol"}

# Page setup
st.set_page_config(page_title="MemoryThing", layout="centered")
st.title("🕊️ MemoryThing – Personalized Memorial Object")
st.markdown("Create a small, symbolic object in memory of someone special.")

# Initialize session state
for key in ["suggestions", "idea_list", "selected_idea", "name", "relationship", "memory"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key != "idea_list" else []

# Load STL mapping from JSON
def load_stl_mapping():
    with open(SUGGESTIONS_JSON, "r") as f:
        return json.load(f)

# Match STL files by filtering generic words
def match_stl_files(suggestion_text, stl_map):
    suggestion_words = set(word.lower().strip(".,") for word in suggestion_text.lower().split())
    suggestion_words -= GENERIC_WORDS

    matched_files = []
    for filename, data in stl_map.items():
        tags = set(tag.lower() for tag in data.get("tags", []))
        filtered_tags = tags - GENERIC_WORDS
        if suggestion_words & filtered_tags:
            matched_files.append(filename)
    return matched_files

# Input form
with st.form("memory_form"):
    name = st.text_input("Your name", value=st.session_state["name"])
    relationship = st.text_input("Who are you remembering?", value=st.session_state["relationship"], placeholder="e.g., My Grandmother")
    memory = st.text_input("What made them special?", value=st.session_state["memory"], placeholder="e.g., She loved sunflowers and baking pies")
    submitted = st.form_submit_button("Generate 3D Object Ideas")

# Generate suggestions
if submitted and relationship and memory:
    st.session_state["name"] = name
    st.session_state["relationship"] = relationship
    st.session_state["memory"] = memory

    with st.spinner("Generating suggestions..."):
        prompt = f"""
You are a helpful assistant that creates personalized small 3D-printable memorial object suggestions.

Relationship: {relationship}
Memory: {memory}

Suggest 2 or 3 emotionally meaningful physical object ideas that are symbolic and small enough to be 3D printed (like keychains, mini charms, tokens). Keep them simple and gentle.
        """
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        suggestions = response.text.strip()
        st.session_state["suggestions"] = suggestions

        idea_list = re.findall(r"(?:[-*]|\d+\.)\s+(.*)", suggestions)
        if not idea_list:
            idea_list = suggestions.split("\n")
        st.session_state["idea_list"] = [i.strip() for i in idea_list if i.strip()]

# Show AI suggestions
if st.session_state["suggestions"]:
    st.markdown("### ✨ Suggestions:")
    options = st.session_state["idea_list"] + ["🔧 None of these – I'll suggest my own"]
    selected_option = st.radio("Choose an idea:", options, key="idea_selector")

    if selected_option == "🔧 None of these – I'll suggest my own":
        custom_text = st.text_area("Describe your custom idea:")
        if st.button("Submit Custom Idea"):
            if not custom_text.strip():
                st.error("Please describe your idea before submitting.")
            else:
                with open(CUSTOM_SUGGESTIONS_FILE, "a") as f:
                    f.write(f"Name: {st.session_state['name']}\n")
                    f.write(f"Relationship: {st.session_state['relationship']}\n")
                    f.write(f"Memory: {st.session_state['memory']}\n")
                    f.write(f"User Custom Idea: {custom_text.strip()}\n")
                    f.write("=" * 50 + "\n")
                st.success("Your idea has been saved. Thank you!")
    else:
        st.session_state["selected_idea"] = selected_option
        stl_mapping = load_stl_mapping()
        matched_files = match_stl_files(selected_option, stl_mapping)

        if matched_files:
            st.success("Matching 3D model(s) found:")
            for matched_file in matched_files:
                with open(os.path.join(STL_FOLDER, matched_file), "rb") as f:
                    st.download_button(label=f"Download: {matched_file}", data=f, file_name=matched_file)
            st.markdown("---")
            st.info("Would you like a custom version of this idea?")
            if st.button("Submit this idea for custom STL creation"):
                with open(CUSTOM_SUGGESTIONS_FILE, "a") as f:
                    f.write(f"Name: {st.session_state['name']}\n")
                    f.write(f"Relationship: {st.session_state['relationship']}\n")
                    f.write(f"Memory: {st.session_state['memory']}\n")
                    f.write(f"Selected AI Idea (STL exists): {selected_option}\n")
                    f.write("Note: STL exists but verify before processing\n")
                    f.write("=" * 50 + "\n")
                st.success("Submitted for custom version. Thank you!")
        else:
            st.warning("No matching STL files found for this idea.")
            if st.button("Submit this idea for custom STL creation"):
                with open(CUSTOM_SUGGESTIONS_FILE, "a") as f:
                    f.write(f"Name: {st.session_state['name']}\n")
                    f.write(f"Relationship: {st.session_state['relationship']}\n")
                    f.write(f"Memory: {st.session_state['memory']}\n")
                    f.write(f"Selected AI Idea (no STL match): {selected_option}\n")
                    f.write("=" * 50 + "\n")
                st.success("Submitted for STL creation. Thank you!")
