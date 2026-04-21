
import asyncio
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from congen.pipeline import VideoGenerationPipeline
from congen.models.script import Script, Scene, VisualDescription, AudioDescription, ScriptMetadata
from congen.config.settings import settings

async def main():
    print("🎅 Setting up Santa Hachuping Project...")

    # 1. Define Paths
    santa_dir = Path("c:/Github/ConGen/santa")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = settings.OUTPUT_DIR / f"{timestamp}_Santa_Hachuping_Mission"
    scenes_dir = output_dir / "2_scenes"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes_dir.mkdir(parents=True, exist_ok=True)

    # 2. Map Images
    # Mapping based on user request and file timestamps
    # image_6 (0번 원본) -> Index 0
    # image_2 -> Index 2 (Assuming (2))
    # image_3 -> Index 3 (Assuming (3))
    # image_4 -> Index 4 (Assuming (4))
    # image_5 -> Index 5 (Assuming 11_09PM, the next one after the (4))
    
    files = sorted([f for f in santa_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']])
    
    # Debug: Print files to be sure
    print("Found files in santa directory:")
    for i, f in enumerate(files):
        print(f"{i}: {f.name}")

    if len(files) < 6:
        print("⚠️ Warning: Not enough files found in santa directory. Proceeding with best guess mapping.")

    # Mapping logic
    image_map = {}
    try:
        image_map['image_6'] = files[0] # 0번 원본
        image_map['image_2'] = files[2] # (2)
        image_map['image_3'] = files[3] # (3)
        image_map['image_4'] = files[4] # (4)
        image_map['image_5'] = files[5] # 11_09PM
    except IndexError:
        print("❌ Error: Could not map images. Please check the santa directory.")
        return

    # 3. Define Scenes
    scenes_data = [
        {
            "id": 1,
            "image": "image_6",
            "duration": 5,
            "visual": "A quiet night in a child's playroom with a jungle gym. Soft dark night lighting. Camera pans slowly over the jungle gym. Cinematic, high quality, 4k.",
            "audio": "Everyone is asleep, a quiet night.",
            "transition": "None"
        },
        {
            "id": 2,
            "image": "image_6", # Transitioning to image_3 look
            "duration": 5,
            "visual": "A mysterious pink light starts glowing on the slide. It swirls and grows into a giant heart-shaped magic portal. The room glows with pink light. Cinematic, magical effects.",
            "audio": "Suddenly, a strange energy surrounds the slide.",
            "transition": "Portal opens"
        },
        {
            "id": 3,
            "image": "image_3", # Transitioning to image_4 look
            "duration": 5,
            "visual": "Santa Hachuping pops out of the portal. Climbing up the slide against gravity with a heavy gift bag. Dynamic movement. The portal behind is shrinking.",
            "audio": "Santa Hachuping appears from the portal!",
            "transition": "Character arrival"
        },
        {
            "id": 4,
            "image": "image_4", # Transitioning to image_2 look
            "duration": 5,
            "visual": "Hachuping reaches the top platform. The portal disappears completely. Hachuping adjusts the Santa hat and looks at the secret space in the net.",
            "audio": "Hachuping successfully reaches the top.",
            "transition": "Reaching goal"
        },
        {
            "id": 5,
            "image": "image_2", # Transitioning to image_5 look
            "duration": 5,
            "visual": "Hachuping enters the net space and opens the big bag. Taking out shiny gift boxes and arranging them. Happy expression. Christmas atmosphere.",
            "audio": "Preparing the gifts in the secret space.",
            "transition": "Mission accomplished"
        },
        {
            "id": 6,
            "image": "image_5", # Transitioning to image_6 look
            "duration": 5,
            "visual": "Hachuping winks at the camera and disappears with magical dust. The room returns to the quiet state. Empty jungle gym.",
            "audio": "Mission complete, Hachuping disappears like magic.",
            "transition": "Departure"
        }
    ]

    script_scenes = []
    for s in scenes_data:
        # Copy image to scenes dir
        src_image = image_map.get(s['image'])
        if not src_image:
            print(f"❌ Missing image for scene {s['id']}")
            continue
            
        dst_image_name = f"scene_{s['id']:03d}.png" # Pipeline expects png extension logic or just uses provided path
        # Actually pipeline uses whatever path is in script, but let's standardize
        dst_image = scenes_dir / dst_image_name
        
        # Convert/Copy
        shutil.copy2(src_image, dst_image)
        
        scene_obj = Scene(
            scene_id=s['id'],
            duration_seconds=s['duration'],
            visual=VisualDescription(description=s['visual']),
            audio=AudioDescription(narration=s['audio']),
            transition=s['transition'],
            image_path=str(dst_image)
        )
        script_scenes.append(scene_obj)

    # 4. Create Script Object
    script = Script(
        metadata=ScriptMetadata(
            title="Santa Hachuping's Secret Mission",
            topic="Christmas Story",
            target_audience="Children",
            learning_objective="Entertainment",
            total_duration_seconds=30,
            style="Cinematic",
            language="ko"
        ),
        scenes=script_scenes
    )

    # 5. Save Script JSON
    script_path = output_dir / "1_script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
    
    print(f"✅ Project setup complete at: {output_dir}")
    
    # 6. Run Pipeline
    print("🚀 Starting Video Generation Pipeline...")
    pipeline = VideoGenerationPipeline()
    await pipeline.run_from_existing(output_dir)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
