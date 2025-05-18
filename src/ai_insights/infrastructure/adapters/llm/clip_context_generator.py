import google.generativeai as genai
import os
import time
import json
from dotenv import load_dotenv

# --- Module-Level Constants and Configuration ---

# Determine project root to correctly locate .env and relative paths
# This assumes clip_context_generator.py is at:
# Supercell_AI_Insights/src/ai_insights/infrastructure/adapters/llm/clip_context_generator.py
try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
except NameError: # Fallback for environments where __file__ might not be defined (e.g. some notebooks)
    PROJECT_ROOT = os.getcwd() # Assume current working directory is project root

DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=DOTENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
_api_key_configured_globally = False

def _ensure_api_key_is_configured():
    """Ensures the Gemini API key is configured. Call before API interactions."""
    global _api_key_configured_globally, GOOGLE_API_KEY
    if _api_key_configured_globally:
        return True

    if not GOOGLE_API_KEY:
        print(f"LLM Service Error: GOOGLE_API_KEY not found. Checked .env at: {DOTENV_PATH}")
        return False
    # Avoid using placeholder key directly in comparisons if possible, check for non-empty and not placeholder
    if GOOGLE_API_KEY == "YOUR_ACTUAL_API_KEY_HERE" or not GOOGLE_API_KEY.strip(): # Common placeholder
        print(f"LLM Service Warning: GOOGLE_API_KEY in .env at {DOTENV_PATH} might be a placeholder or is empty.")
        return False
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("LLM Service: Gemini API Key configured successfully.")
        _api_key_configured_globally = True
        return True
    except Exception as e:
        print(f"LLM Service Error: Could not configure Google API: {e}")
        return False

# --- Private Helper Functions ---

def _resolve_path(base_dir_relative_to_root: str, filename: str = "") -> str:
    """Resolves a path relative to the project root."""
    return os.path.join(PROJECT_ROOT, base_dir_relative_to_root, filename)

def _analyze_clip_with_gemini(video_path: str, user_provided_context: str) -> dict:
    """
    Core Gemini analysis function.
    """
    video_filename = os.path.basename(video_path) # Use actual filename as ID
    if not os.path.exists(video_path): # video_path should be absolute here
        return {"video_id": video_filename, "error": f"Video file not found at '{video_path}'."}

    if not _api_key_configured_globally:
        # Attempt to configure if not already, in case of direct function call
        if not _ensure_api_key_is_configured():
             return {"video_id": video_filename, "error": "Google API Key not configured."}

    video_file_resource = None
    try:
        print(f"LLM Service: Uploading video '{video_filename}' from '{video_path}'...")
        video_file_resource = genai.upload_file(path=video_path)

        while video_file_resource.state.name == "PROCESSING":
            print(f"LLM Service: Video '{video_filename}' processing (state: {video_file_resource.state.name})...")
            time.sleep(2) 
            video_file_resource = genai.get_file(video_file_resource.name)

        if video_file_resource.state.name == "FAILED":
            return {"video_id": video_filename, "error": f"Gemini API failed to process video '{video_file_resource.name}'."}
        
        print(f"LLM Service: Video '{video_filename}' processed (state: {video_file_resource.state.name}).")

        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        full_prompt = f"""
        You are an expert eSports analyst for Brawl Stars.
        Analyze the provided video clip. Your goal is to generate a concise, exciting, Brawler-focused description of the key play,
        no more than two lines (approx. 30-50 words).

        IMPORTANT:
        - Focus ONLY on Brawlers by their Brawler name (e.g., Shelly, Colt), their actions, and their abilities (Supers, Gadgets, Star Powers).
        - Do NOT mention player names, usernames, or team names, even if visible. The description is about Brawler actions.

        Use the following user-provided context/metadata to guide your analysis:
        --- USER CONTEXT/METADATA ---
        {user_provided_context}
        --- END USER CONTEXT/METADATA ---

        Based on the video and the user context/metadata, ensure your description includes:
        1. Key Brawlers involved and their significant actions.
        2. Crucial Brawler abilities (Gadget, Star Power, Super) used and their impact.
        3. The climax of the play in terms of Brawler interactions.

        Example of desired output (Brawler-focused):
        "Mortis dodges shots with 'Survival Shovel', then uses 'Combo Spinner' to eliminate a vulnerable Piper. El Primo jumps in with his Super, but misses!"

        Now, analyze the video and generate the Brawler-focused description:
        """
        print(f"LLM Service: Generating content for '{video_filename}'...")
        response = model.generate_content([full_prompt, video_file_resource])
        return {"video_id": video_filename, "description": response.text.strip()}
    except Exception as e:
        error_message = f"LLM Service: Error during analysis of '{video_filename}': {str(e)}"
        # Check for common API error patterns
        if "permission_denied" in str(e).lower() or \
           "authentication" in str(e).lower() or \
           "api key" in str(e).lower() or \
           any(code in str(e) for code in ["400", "401", "403", "429"]): # Bad Request, Unauthorized, Forbidden, Too Many Requests
            error_message = f"LLM Service: API communication error for '{video_filename}'. Check API Key/quota/permissions. Details: {str(e)}"
        return {"video_id": video_filename, "error": error_message}
    finally:
        if video_file_resource and hasattr(video_file_resource, 'name') and video_file_resource.name:
            try:
                genai.delete_file(video_file_resource.name)
            except Exception as e_del:
                print(f"LLM Service Warning: Could not delete API file {video_file_resource.name}. Error: {e_del}")

def _find_video_path(brawler_name: str, videos_dir_relative: str, specific_video_filename: str = None) -> str | None:
    """Finds the absolute path to a video file."""
    abs_videos_dir = _resolve_path(videos_dir_relative)

    if specific_video_filename:
        potential_path = os.path.join(abs_videos_dir, specific_video_filename)
        if os.path.isfile(potential_path): # Check if it's a file
            return potential_path
        else:
            print(f"LLM Service: Specified video file '{specific_video_filename}' not found in '{abs_videos_dir}'.")
            return None

    if not os.path.isdir(abs_videos_dir):
        print(f"LLM Service Error: Videos directory '{abs_videos_dir}' not found.")
        return None
        
    found_videos = []
    for f_name in os.listdir(abs_videos_dir):
        if brawler_name.lower() in f_name.lower() and f_name.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
            found_videos.append(os.path.join(abs_videos_dir, f_name))
    
    if not found_videos:
        print(f"LLM Service: No video files found for Brawler '{brawler_name}' in '{abs_videos_dir}'. Searched for filenames containing '{brawler_name}'.")
        return None
    
    if len(found_videos) > 1:
        print(f"LLM Service Warning: Multiple videos found for '{brawler_name}': {[os.path.basename(v) for v in found_videos]}.")
        print(f"Using the first one found: '{os.path.basename(found_videos[0])}'. Use --video_filename from CLI for a specific clip.")
    return found_videos[0]

def _load_context_text(brawler_name: str, contexts_dir_relative: str, specific_context_filename: str = None) -> str:
    """Loads context text from a file."""
    abs_contexts_dir = _resolve_path(contexts_dir_relative)
    default_context_content = f"Default context: Analyze key actions for Brawler {brawler_name.capitalize()}, their abilities, and the overall play. If {brawler_name.capitalize()} is not central, describe the main Brawler action."
    
    path_to_try = None
    if specific_context_filename:
        path_to_try = os.path.join(abs_contexts_dir, specific_context_filename)
        if not os.path.exists(path_to_try):
            print(f"LLM Service Warning: Specified context file '{path_to_try}' not found.")
            path_to_try = None # Reset to allow fallback search
    
    if not path_to_try:
        brawler_specific_path = os.path.join(abs_contexts_dir, f"{brawler_name.lower()}_context.txt")
        if os.path.exists(brawler_specific_path):
            path_to_try = brawler_specific_path
        else:
            default_txt_path = os.path.join(abs_contexts_dir, "default_context.txt")
            if os.path.exists(default_txt_path):
                path_to_try = default_txt_path

    if path_to_try and os.path.exists(path_to_try):
        try:
            with open(path_to_try, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"LLM Service: Loaded context from: {path_to_try}")
                return content
        except Exception as e:
            print(f"LLM Service Warning: Could not read context file {path_to_try}. Error: {e}. Using hardcoded default.")
            return default_context_content
    else:
        print(f"LLM Service Info: No suitable context file found in '{abs_contexts_dir}' (tried specific, brawler-specific, and default.txt). Using hardcoded default.")
        return default_context_content

def _ensure_directory_exists(dir_relative_to_root: str):
    """Creates a directory if it doesn't exist, path relative to project root."""
    abs_dir_path = _resolve_path(dir_relative_to_root)
    if not os.path.exists(abs_dir_path):
        try:
            os.makedirs(abs_dir_path)
            print(f"LLM Service: Created directory: {abs_dir_path}")
        except OSError as e:
            print(f"LLM Service Error: Could not create directory {abs_dir_path}. Error: {e}")


# --- Public Function for CLI/Application to Call ---
def generate_clip_analysis(
        brawler_name: str,
        videos_dir_relative: str = "data/raw/clips/",
        contexts_dir_relative: str = "data/raw/context/",
        video_filename_override: str = None,
        context_filename_override: str = None
    ) -> list:
    """
    Generates analysis for a video clip related to a specific Brawler.
    This function is intended to be called by other parts of the application, like a CLI.

    Args:
        brawler_name (str): The name of the Brawler (e.g., "hank").
        videos_dir_relative (str): Path to video clips dir, relative to project root.
        contexts_dir_relative (str): Path to context files dir, relative to project root.
        video_filename_override (str, optional): Exact video filename in videos_dir_relative.
        context_filename_override (str, optional): Exact context filename in contexts_dir_relative.

    Returns:
        list: A list containing a single dictionary with the analysis result,
              e.g., [{"video_id": "filename.mp4", "description": "..." | "error": "..."}].
              Returns empty list or error dict if critical setup fails.
    """
    if not _ensure_api_key_is_configured(): # Crucial first step
        return [{"video_id": video_filename_override or f"{brawler_name}_clip", "error": "API Key not configured. Cannot proceed."}]

    # Ensure directories exist to avoid errors later, also helps first-time users.
    _ensure_directory_exists(videos_dir_relative)
    _ensure_directory_exists(contexts_dir_relative)
    
    # Suggest creating a sample context file if none exists for the brawler
    # This helps users understand where to put context files.
    abs_contexts_dir = _resolve_path(contexts_dir_relative)
    sample_brawler_context_path = os.path.join(abs_contexts_dir, f"{brawler_name.lower()}_context.txt")
    if not os.path.exists(sample_brawler_context_path) and not context_filename_override: # Only if no specific override
        try:
            with open(sample_brawler_context_path, 'w', encoding='utf-8') as f_sample:
                f_sample.write(f"# Context for Brawler: {brawler_name.capitalize()}\n"
                               f"# This is an auto-generated sample. Please edit with specific details.\n"
                               f"Game Mode Hint: [e.g., Gem Grab, Brawl Ball, Showdown]\n"
                               f"Focus on: [e.g., {brawler_name.capitalize()}'s Super usage, defensive plays with Gadgets, combos]\n"
                               f"Brawlers of Interest (besides {brawler_name.capitalize()}): [e.g., Mortis, Crow if they interact significantly]\n"
                               f"Desired Tone: [e.g., Exciting, Analytical, Humorous]\n")
            print(f"LLM Service Hint: A sample context file for '{brawler_name}' has been created at: {sample_brawler_context_path}. Please edit it.")
        except Exception as e_create:
            print(f"LLM Service Warning: Could not create sample context file for {brawler_name} at {sample_brawler_context_path}. Error: {e_create}")


    video_abs_path = _find_video_path(brawler_name, videos_dir_relative, video_filename_override)
    
    if not video_abs_path:
        error_video_id = video_filename_override if video_filename_override else f"{brawler_name}_video_not_found"
        return [{"video_id": error_video_id, "error": f"Suitable video for Brawler '{brawler_name}' not found in '{_resolve_path(videos_dir_relative)}'."}]

    context_text = _load_context_text(brawler_name, contexts_dir_relative, context_filename_override)
    
    print(f"\nLLM Service: Initiating analysis for video: {os.path.basename(video_abs_path)}")
    # Print a concise version of the context being used
    context_snippet = context_text.replace('\n', ' ').strip()
    print(f"LLM Service: Using context (first 100 chars): '{context_snippet[:100]}...'")

    analysis_result_dict = _analyze_clip_with_gemini(video_abs_path, context_text)
    
    return [analysis_result_dict] if analysis_result_dict else []