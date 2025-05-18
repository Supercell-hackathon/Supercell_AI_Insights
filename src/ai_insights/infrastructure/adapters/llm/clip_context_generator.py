import google.generativeai as genai
import os
import time
import json
from dotenv import load_dotenv

try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
except NameError: 
    PROJECT_ROOT = os.getcwd() # Fallback

DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
_api_key_configured_globally = False

def _ensure_api_key_is_configured():
    """Ensures the Gemini API key is configured."""
    global _api_key_configured_globally, GEMINI_API_KEY 
    if _api_key_configured_globally:
        return True
    
    if not GEMINI_API_KEY: 
        if os.path.exists(DOTENV_PATH):
            load_dotenv(dotenv_path=DOTENV_PATH)
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        else:
            print(f"LLM Service Info: .env file not found at {DOTENV_PATH} for API key loading by this module.")

    if not GEMINI_API_KEY:
        print(f"LLM Service Error: GEMINI_API_KEY not found after checking environment and .env.")
        return False
    if GEMINI_API_KEY.strip() == "" or "YOUR_ACTUAL_API_KEY_HERE" in GEMINI_API_KEY or "AIzaSy" not in GEMINI_API_KEY : # Simple check
        print(f"LLM Service Warning: GEMINI_API_KEY in .env (path: {DOTENV_PATH}) appears to be a placeholder, empty, or invalid.")
        return False
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("LLM Service: Gemini API Key configured successfully.")
        _api_key_configured_globally = True
        return True
    except Exception as e:
        print(f"LLM Service Error: Could not configure Google API with key: {e}")
        return False

def _resolve_path(base_dir_relative_to_root: str, filename: str = "") -> str:
    """Resolves a path to be absolute from the project root."""
    return os.path.join(PROJECT_ROOT, base_dir_relative_to_root, filename)

def _analyze_clip_with_gemini(video_path: str, user_provided_context: str) -> dict:
    """Internal core Gemini analysis function."""
    video_filename = os.path.basename(video_path)
    if not os.path.exists(video_path): 
        return {"video_id": video_filename, "error": f"Video file not found at '{video_path}'."}
    
    if not _api_key_configured_globally: 
         print("LLM Service Error: API key not configured prior to Gemini call.")
         return {"video_id": video_filename, "error": "Google API Key not configured before Gemini call."}

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
        no more than two lines (approximately 30-50 words).

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
        if any(code in str(e).lower() for code in ["permission_denied", "authentication", "api key", "400", "401", "403", "429"]):
            error_message = f"LLM Service: API communication error for '{video_filename}'. Check API Key/quota/permissions. Details: {str(e)}"
        return {"video_id": video_filename, "error": error_message}
    finally:
        if video_file_resource and hasattr(video_file_resource, 'name') and video_file_resource.name:
            try:
                genai.delete_file(video_file_resource.name)
            except Exception as e_del:
                print(f"LLM Service Warning: Could not delete API file {video_file_resource.name}. Error: {e_del}")

def _find_video_path(brawler_name: str, videos_dir_relative: str) -> str | None:
    """Finds the absolute path to a video file for the given brawler."""
    abs_videos_dir = _resolve_path(videos_dir_relative)
    if not os.path.isdir(abs_videos_dir):
        print(f"LLM Service Error: Videos directory '{abs_videos_dir}' not found.")
        return None
        
    found_videos = []
    for f_name in os.listdir(abs_videos_dir):
        if brawler_name.lower() in f_name.lower() and f_name.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
            found_videos.append(os.path.join(abs_videos_dir, f_name))
    
    if not found_videos:
        print(f"LLM Service: No video files found for Brawler '{brawler_name}' in '{abs_videos_dir}' (searched for filenames containing '{brawler_name.lower()}').")
        return None
    
    if len(found_videos) > 1:
        found_videos.sort() 
        print(f"LLM Service Warning: Multiple videos found for '{brawler_name}': {[os.path.basename(v) for v in found_videos]}.")
        print(f"Using the first one found (alphabetically): '{os.path.basename(found_videos[0])}'.")
    return found_videos[0]

def _load_context_text(brawler_name: str, contexts_dir_relative: str) -> tuple[str, str | None]:
    """Loads context text. Returns (context_string, path_of_file_loaded_or_None)."""
    abs_contexts_dir = _resolve_path(contexts_dir_relative)
    hardcoded_default_context = (
        f"Default context: Analyze key actions for Brawler {brawler_name.capitalize()}. "
        f"Focus on abilities and overall impact. If {brawler_name.capitalize()} "
        f"is not central, describe the main Brawler action in the clip."
    )
    
    path_to_try = None
    path_actually_used = None 
    brawler_specific_ctx_file = os.path.join(abs_contexts_dir, f"{brawler_name.lower()}_context.txt")
    general_default_ctx_file = os.path.join(abs_contexts_dir, "default_context.txt")

    if os.path.exists(brawler_specific_ctx_file):
        path_to_try = brawler_specific_ctx_file
    elif os.path.exists(general_default_ctx_file):
        path_to_try = general_default_ctx_file

    if path_to_try:
        try:
            with open(path_to_try, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            print(f"LLM Service: Loaded context from: {path_to_try}")
            path_actually_used = path_to_try 
            return content, path_actually_used
        except Exception as e:
            print(f"LLM Service Warning: Could not read context file {path_to_try}. Error: {e}. Using hardcoded default.")
            return hardcoded_default_context, None 
    else:
        print(f"LLM Service Info: No specific context file for '{brawler_name}' (e.g., '{brawler_specific_ctx_file}') "
              f"or general default ('{general_default_ctx_file}') found in '{abs_contexts_dir}'. Using hardcoded default.")
        return hardcoded_default_context, None

def _ensure_directory_exists(dir_relative_to_root: str):
    """Creates a directory if it doesn't exist. Path is relative to project root."""
    abs_dir_path = _resolve_path(dir_relative_to_root)
    if not os.path.exists(abs_dir_path):
        try:
            os.makedirs(abs_dir_path)
            print(f"LLM Service: Created directory: {abs_dir_path}")
        except OSError as e:
            if not os.path.isdir(abs_dir_path):
                 print(f"LLM Service Error: Could not create directory {abs_dir_path}. Error: {e}")

def _create_sample_context_if_needed(brawler_name: str, contexts_dir_relative: str, path_of_context_file_used: str | None):
    """Creates a sample context file for the brawler if no actual context file was successfully loaded."""
    abs_contexts_dir = _resolve_path(contexts_dir_relative)
    brawler_specific_sample_path = os.path.join(abs_contexts_dir, f"{brawler_name.lower()}_context.txt")

    if path_of_context_file_used is None and not os.path.exists(brawler_specific_sample_path):
        try:
            _ensure_directory_exists(contexts_dir_relative) 
            with open(brawler_specific_sample_path, 'w', encoding='utf-8') as f_sample:
                f_sample.write(f"# Context for Brawler: {brawler_name.capitalize()}\n")
                f_sample.write(f"# This is an auto-generated sample. Please edit with specific details for '{brawler_name}'.\n\n")
                f_sample.write(f"Game Mode Hint: [e.g., Gem Grab, Brawl Ball, Showdown]\n")
                f_sample.write(f"Focus on: [e.g., {brawler_name.capitalize()}'s Super usage, defensive plays with Gadgets, interesting combos]\n")
                f_sample.write(f"Brawlers of Interest (besides {brawler_name.capitalize()}): [e.g., Mortis, Crow, or specific counters/synergies if relevant to the clip type]\n")
                f_sample.write(f"Desired Tone: [e.g., Exciting, Analytical, Humorous, Tactical]\n")
                f_sample.write(f"Other specific instructions: [e.g., 'note any misplays', 'highlight teamwork if visible']\n")
            print(f"LLM Service Hint: A sample context file for '{brawler_name}' has been created at: {brawler_specific_sample_path}. Please edit it for best results.")
        except Exception as e_create:
            print(f"LLM Service Warning: Could not create sample context file for {brawler_name} at {brawler_specific_sample_path}. Error: {e_create}")

def brawler_clip_analysis( 
        brawler_name: str,
        videos_dir_relative_to_root: str = "data/raw/clips/",
        contexts_dir_relative_to_root: str = "data/raw/context/"
    ):
    output_json_dir_relative_to_root = "data/raw/clip_context/" 
    output_filename = f"{brawler_name.lower()}_clip_context.json"

    print(f"LLM Service: Request to analyze clip for Brawler '{brawler_name}'.")
    print(f"LLM Service: Output will be saved to '{os.path.join(output_json_dir_relative_to_root, output_filename)}' (relative to project root).")

    if not _ensure_api_key_is_configured():
        result_to_save = [{"video_id": f"{brawler_name}_clip", "error": "API Key not configured for LLM Service."}]
    else:
        _ensure_directory_exists(videos_dir_relative_to_root)
        _ensure_directory_exists(contexts_dir_relative_to_root)
        _ensure_directory_exists(output_json_dir_relative_to_root)

        context_text_for_analysis, path_of_context_file_used = _load_context_text(
            brawler_name, contexts_dir_relative_to_root
        )
        
        _create_sample_context_if_needed(brawler_name, contexts_dir_relative_to_root, path_of_context_file_used)

        video_absolute_path = _find_video_path(brawler_name, videos_dir_relative_to_root)
        
        analysis_data_list = [] 
        if not video_absolute_path:
            error_video_id = f"{brawler_name}_video_not_found" 
            analysis_data_list.append({
                "video_id": error_video_id, 
                "error": f"Video for Brawler '{brawler_name}' not found in '{_resolve_path(videos_dir_relative_to_root)}'."
            })
        else:
            print(f"\nLLM Service: Analyzing video: {os.path.basename(video_absolute_path)}")
            context_snippet = context_text_for_analysis.replace('\n', ' ').strip()
            print(f"LLM Service: Using context (first 100 chars): '{context_snippet[:100]}...'")
            
            analysis_result_dictionary = _analyze_clip_with_gemini(video_absolute_path, context_text_for_analysis)
            
            if analysis_result_dictionary:
                analysis_data_list.append(analysis_result_dictionary)
        
        result_to_save = analysis_data_list

    output_filepath_absolute = _resolve_path(output_json_dir_relative_to_root, output_filename) 
    try:
        with open(output_filepath_absolute, 'w', encoding='utf-8') as f:
            json.dump(result_to_save, f, ensure_ascii=False, indent=4)
        print(f"LLM Service: Analysis result saved/overwritten: {output_filepath_absolute}")
    except IOError as e: 
        print(f"LLM Service Error: Could not save JSON to '{output_filepath_absolute}': {e}")
        print("LLM Service Result (console output instead due to save error):\n", json.dumps(result_to_save, ensure_ascii=False, indent=4))
    except TypeError as e: 
        print(f"LLM Service Error: Could not serialize result to JSON for '{output_filepath_absolute}': {e}")
        print("LLM Service Result (raw data that failed serialization):\n", result_to_save)
    
    print("\nLLM Service: Brawler clip analysis process finished.")