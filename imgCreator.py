from openai import OpenAI
import base64
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import datetime
import json
import requests
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

def generate_image(all_scenes: str, selected_scene: int, scene_script: str, scene_keyword: str, output_filename: Optional[str] = None, model: str = "dall-e-3") -> str:
    if output_filename is None:
        output_filename = f"scene_{selected_scene}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    client = OpenAI()

    image_prompt = f"""Create a webtoon/manhwa style illustration for scene {selected_scene} of an advertising comic.

    CONTEXT - Full Story Flow:
    {all_scenes}

    CURRENT SCENE ({selected_scene}):
    Script: {scene_script}
    Main Keyword: {scene_keyword}

    VISUAL REQUIREMENTS:
    - Korean webtoon/manhwa art style with clean lines and vibrant colors
    - Single panel comic book illustration
    - Character should be relatable Korean person (20s-40s)
    - Focus on the emotion and situation described in the script
    - Include visual elements that match the main keyword
    - Composition should work well in vertical mobile format
    - Use appropriate lighting and mood for the scene's emotional tone
    - Show clear facial expressions and body language
    - Include relevant background elements that support the story

    SCENE POSITION CONTEXT:
    - This is scene {selected_scene} out of 18 total scenes
    - Maintain visual consistency with the overall advertising narrative
    - Character appearance should be consistent throughout the story

    Style: Clean Korean webtoon art, professional quality, detailed illustration, expressive characters, advertising comic aesthetic."""
        
    response = client.images.generate(
        model=model,
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    
    image_url = response.data[0].url
    image_response = requests.get(image_url)
    
    if image_response.status_code == 200:
        with open(output_filename, "wb") as f:
            f.write(image_response.content)
        return output_filename

def load_scenes_from_json(json_file_path: str) -> dict:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_all_scenes_context(scenes_data: dict) -> str:
    context = "COMPLETE STORY CONTEXT (All 18 Scenes):\n"
    for scene_key, scene_data in scenes_data['scenes'].items():
        scene_num = scene_key.replace('scene_', '')
        context += f"Scene {scene_num}: {scene_data['script']} (키워드: {scene_data['main_keyword']})\n"
    return context

def generate_scene_image(json_file_path: str, scene_number: int, output_dir: str = "images") -> str:
    scenes_data = load_scenes_from_json(json_file_path)
    
    if scene_number < 1 or scene_number > 18:
        raise ValueError("Scene number must be between 1 and 18")
    
    scene_key = f"scene_{scene_number}"
    if scene_key not in scenes_data['scenes']:
        raise ValueError(f"Scene {scene_number} not found in the data")
    
    scene_data = scenes_data['scenes'][scene_key]
    scene_script = scene_data['script']
    scene_keyword = scene_data['main_keyword']
    
    all_scenes_context = create_all_scenes_context(scenes_data)
    output_filename = os.path.join(output_dir, f"scene_{scene_number}.png")
    
    image_path = generate_image(
        all_scenes=all_scenes_context,
        selected_scene=scene_number,
        scene_script=scene_script,
        scene_keyword=scene_keyword,
        output_filename=output_filename
    )
    
    return image_path

def generate_all_scenes_with_rate_limit(json_file_path: str, output_dir: str = "images") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    scenes_data = load_scenes_from_json(json_file_path)
    all_scenes_context = create_all_scenes_context(scenes_data)
    
    print(f"⏱️  Processing with rate limit: 5 images per minute (12 second intervals)")
    
    for scene_num in range(1, 19):
        try:
            print(f"🎨 Processing Scene {scene_num}/18...")
            
            scene_key = f"scene_{scene_num}"
            scene_data = scenes_data['scenes'][scene_key]
            scene_script = scene_data['script']
            scene_keyword = scene_data['main_keyword']
            
            output_filename = os.path.join(output_dir, f"scene_{scene_num}.png")
            
            image_path = generate_image(
                all_scenes=all_scenes_context,
                selected_scene=scene_num,
                scene_script=scene_script,
                scene_keyword=scene_keyword,
                output_filename=output_filename
            )
            
            results[scene_num] = image_path
            print(f"✅ Scene {scene_num} completed: {image_path}")
            
            if scene_num < 18:
                print(f"⏳ Waiting 12 seconds to respect rate limit...")
                time.sleep(12)
            
        except Exception as e:
            print(f"❌ Scene {scene_num} failed: {e}")
            results[scene_num] = None
    
    return results

if __name__ == "__main__":

    json_file = "result4.json"
    output_folder = "test_2"

    
    print(f"🚀 Generating all 18 scenes sequentially...")
    print(f"📁 Input: {json_file}")
    print(f"📁 Output: {output_folder}/")
    print(f"⏱️  Estimated time: ~3.6 minutes (12 sec intervals)")
    
    start_time = time.time()
    results = generate_all_scenes_with_rate_limit(json_file, output_folder)
    end_time = time.time()
    
    successful = sum(1 for r in results.values() if r is not None)
    total_time = int(end_time - start_time)
    
    print(f"\n📊 Results: {successful}/18 scenes generated successfully")
    print(f"⏱️  Total time: {total_time//60}m {total_time%60}s")
    
    for scene_num in range(1, 19):
        status = "✅" if results.get(scene_num) else "❌"
        print(f"  Scene {scene_num}: {status}")
