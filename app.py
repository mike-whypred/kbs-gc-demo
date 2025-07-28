import streamlit as st
from openai import OpenAI
import time
import random
import requests
from PIL import Image
import base64

# Configuration
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
LEONARDO_API_KEY = st.secrets.get("LEORNADO_API_KEY", "")  # Note: keeping the misspelled key name as it exists in secrets.toml
APP_MODE = st.secrets.get("APP_MODE", "test")
S3_BUCKET_URL = st.secrets.get("S3_BUCKET_URL", "https://your-s3-bucket.s3.amazonaws.com")

# Configure page
st.set_page_config(
    page_title="KBS AI Campaign Generator",
    page_icon="🏆",
    #layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f2937;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #6b7280;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .powered-by {
        text-align: center;
        color: #9ca3af;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .campaign-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .genre-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        cursor: pointer;
    }
    .success-message {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: #065f46;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-weight: bold;
    }
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
    }
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        animation: spin 1s linear infinite;
        margin-bottom: 2rem;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loading-text {
        font-size: 1.5rem;
        color: #667eea;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .loading-subtext {
        font-size: 1rem;
        color: #6b7280;
    }
    .regenerate-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .regenerate-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'auth'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'team_name' not in st.session_state:
    st.session_state.team_name = ""
if 'briefs' not in st.session_state:
    st.session_state.briefs = []
if 'selected_brief' not in st.session_state:
    st.session_state.selected_brief = None
if 'images' not in st.session_state:
    st.session_state.images = []
if 'selected_images' not in st.session_state:
    st.session_state.selected_images = []
if 'selected_genre' not in st.session_state:
    st.session_state.selected_genre = None
if 'generated_song' not in st.session_state:
    st.session_state.generated_song = None
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = []

# OpenAI client setup
client = None
if OPENAI_API_KEY and APP_MODE == "production":
    try:
        #openai.api_key = OPENAI_API_KEY
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI client: {e}")
        # App will fall back to test mode if client initialization fails

# Sample data for test mode
SAMPLE_IMAGES = [
    "https://images.pexels.com/photos/358042/pexels-photo-358042.jpeg",
    "https://images.pexels.com/photos/1752757/pexels-photo-1752757.jpeg",
    "https://images.pexels.com/photos/1884574/pexels-photo-1884574.jpeg",
    "https://images.pexels.com/photos/262524/pexels-photo-262524.jpeg",
    "https://images.pexels.com/photos/1884576/pexels-photo-1884576.jpeg"
]

SONG_GENRES = [
    {
        "id": "rock-anthem",
        "name": "Rock Anthem",
        "description": "High-energy rock with powerful vocals and driving guitar riffs perfect for victory celebrations",
        "emoji": "⚡"
    },
    {
        "id": "electronic-hype", 
        "name": "Electronic Hype",
        "description": "Modern electronic beats with synthetic energy to pump up crowds and create excitement",
        "emoji": "🎵"
    },
    {
        "id": "orchestral-epic",
        "name": "Orchestral Epic", 
        "description": "Cinematic orchestral composition with dramatic crescendos for triumphant moments",
        "emoji": "🎼"
    },
    {
        "id": "inspirational-pop",
        "name": "Inspirational Pop",
        "description": "Uplifting pop melody with emotional lyrics that resonates with fans of all ages", 
        "emoji": "❤️"
    }
]

# Helper functions
def generate_brief(team_name, brief_type="brief1"):
    if APP_MODE == "test":
        time.sleep(2)  # Simulate API delay
        
        if brief_type == "brief1":
            return f"""# {team_name}

## Core Narrative
{team_name} represents the pinnacle of athletic excellence, community unity, and unwavering determination. This campaign celebrates not just the team's prowess on the field, but their role as hometown heroes who inspire greatness in every fan.

## Key Themes
- **Legacy & Tradition:** Honoring decades of championship spirit
- **Community Pride:** Bringing the city together under one banner
- **Unstoppable Force:** Showcasing athletic dominance and teamwork
- **Fan Devotion:** Celebrating the passionate fanbase that fuels victory

## Campaign Vision
Create an emotional connection that transforms casual viewers into lifelong supporters, emphasizing how {team_name} embodies the fighting spirit of their community."""
        else:
            return f"""# {team_name}

## Strategic Narrative
{team_name} stands as a beacon of excellence, representing more than just athletic achievement – they embody the dreams, aspirations, and collective spirit of an entire community.

## Core Pillars
- **Innovation & Excellence:** Pushing boundaries in every game
- **Unity in Diversity:** Bringing together fans from all walks of life
- **Resilience & Grit:** Overcoming challenges with determination
- **Championship Mentality:** Setting the standard for success

## Creative Direction
Develop a campaign that showcases {team_name} as both fierce competitors and community champions, creating an aspirational brand that resonates with fans' personal values and ambitions."""
    
    # Production mode - use OpenAI
    try:
        if brief_type == "brief1":
            prompt = f"""Create a comprehensive marketing campaign brief for the sports team "{team_name}". 

Format the response in markdown with the following structure:
# {team_name}

## Core Narrative
[Write a compelling narrative about the team's identity and values]

## Key Themes
- **[Theme 1]:** [Description]
- **[Theme 2]:** [Description]
- **[Theme 3]:** [Description] 
- **[Theme 4]:** [Description]

## Campaign Vision
[Describe the overall vision and goals for the marketing campaign]

Focus on themes like legacy, community, excellence, and passion. Make it inspiring and emotionally engaging."""
        else:
            prompt = f"""Create a comprehensive marketing campaign brief for the sports team "{team_name}".

Format the response in markdown with the following structure:
# {team_name}

## Strategic Narrative
[Write about the team's role in the community and their broader impact]

## Core Pillars
- **[Pillar 1]:** [Description]
- **[Pillar 2]:** [Description]
- **[Pillar 3]:** [Description]
- **[Pillar 4]:** [Description]

## Creative Direction
[Describe the creative approach and messaging strategy]

Focus on themes like innovation, unity, resilience, and championship mentality. Make it aspirational and community-focused."""
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a professional marketing strategist creating campaign briefs for sports teams. Write compelling, emotionally engaging content in markdown format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating brief: {e}")
        return generate_brief(team_name, brief_type)  # Fallback to test mode

def generate_images(brief, count=1):  # Changed to generate just 1 image
    # Clear previous debug info
    st.session_state.debug_info = []
    
    if APP_MODE == "test":
        st.session_state.debug_info.append("🧪 Running in TEST mode - using sample images")
        time.sleep(4)  # Simulate API delay
        random.shuffle(SAMPLE_IMAGES)
        return SAMPLE_IMAGES[:1]  # Return just 1 image in test mode
    
    # Debug: Check configuration
    st.session_state.debug_info.append(f"📊 APP_MODE = {APP_MODE}")
    st.session_state.debug_info.append(f"🔑 Leonardo API Key Present: {'Yes' if LEONARDO_API_KEY else 'No'}")
    st.session_state.debug_info.append(f"📏 Leonardo API Key Length: {len(LEONARDO_API_KEY) if LEONARDO_API_KEY else 0}")
    
    print(f"DEBUG: APP_MODE = {APP_MODE}")
    print(f"DEBUG: LEONARDO_API_KEY present = {'Yes' if LEONARDO_API_KEY else 'No'}")
    print(f"DEBUG: LEONARDO_API_KEY length = {len(LEONARDO_API_KEY) if LEONARDO_API_KEY else 0}")
    
    # Production mode - use GPT-4o-mini for prompt and Leonardo AI for image generation
    try:
        team_name = brief.split('\n')[0].replace('# ', '')
        
        # First, use GPT-4o-mini to summarize the brief into a single concise image prompt
        st.session_state.debug_info.append("🤖 Generating image prompt with GPT-4o-mini...")
        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at creating concise, visual image prompts for marketing campaigns. Convert the campaign brief into one powerful, detailed image prompt that captures the essence of the campaign."},
                {"role": "user", "content": f"Convert this campaign brief into ONE powerful image prompt for a marketing visual:\n\n{brief}\n\nThe prompt should be 1-2 sentences, highly visual and descriptive, perfect for generating a stunning marketing campaign image."}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Get the prompt from the response
        prompt = summary_response.choices[0].message.content.strip()
        st.session_state.debug_info.append(f"✅ Generated prompt: {prompt}")
        
        # If the prompt is empty or too short, use a fallback
        if not prompt or len(prompt) < 20:
            prompt = f"Professional sports marketing poster featuring {team_name}, dynamic action shot with team colors, championship trophy, energetic crowd in background, high-quality stadium lighting, inspirational and powerful composition"
            st.session_state.debug_info.append("⚠️ Using fallback prompt")
        
        # Add marketing campaign prefix to the prompt
        prompt = f"Create a marketing campaign for {prompt}"
        st.session_state.debug_info.append(f"🎯 Final prompt: {prompt}")
        
        # Use Leonardo AI for image generation
        leonardo_url = "https://cloud.leonardo.ai/api/rest/v1/generations"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {LEONARDO_API_KEY}",
            "content-type": "application/json"
        }
        
        data = {
            "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
            "contrast": 3.5,
            "prompt": prompt,
            "num_images": 1,
            "width": 1792,
            "height": 1024,
            "alchemy": True,
            "styleUUID": "111dc692-d470-4eec-b791-3475abac4c46",
            "enhancePrompt": False
        }
        
        # Make the API request to Leonardo AI
        st.session_state.debug_info.append("🎨 Sending request to Leonardo AI...")
        print(f"DEBUG: Making Leonardo AI request to {leonardo_url}")
        print(f"DEBUG: Request data = {data}")
        response = requests.post(leonardo_url, headers=headers, json=data)
        
        st.session_state.debug_info.append(f"📡 Leonardo AI Response Status: {response.status_code}")
        print(f"DEBUG: Leonardo AI response status = {response.status_code}")
        print(f"DEBUG: Leonardo AI response = {response.text[:500]}...")
        
        if response.status_code == 200:
            response_data = response.json()
            generation_id = response_data.get("sdGenerationJob", {}).get("generationId")
            
            if generation_id:
                st.session_state.debug_info.append(f"🔗 Generation ID: {generation_id}")
                # Poll for completion - try multiple times with longer waits
                max_attempts = 6
                for attempt in range(max_attempts):
                    time.sleep(5)  # Wait 5 seconds between checks
                    st.session_state.debug_info.append(f"⏳ Polling attempt {attempt + 1}/{max_attempts}")
                    
                    # Get the generated image
                    get_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
                    get_response = requests.get(get_url, headers=headers)
                    
                    st.session_state.debug_info.append(f"📥 Poll Status: {get_response.status_code}")
                    if get_response.status_code == 200:
                        generation_data = get_response.json()
                        
                        # Check multiple possible response structures
                        generated_images = None
                        if "generations_by_pk" in generation_data:
                            generated_images = generation_data["generations_by_pk"].get("generated_images", [])
                        elif "generated_images" in generation_data:
                            generated_images = generation_data["generated_images"]
                        elif "images" in generation_data:
                            generated_images = generation_data["images"]
                        
                        if generated_images and len(generated_images) > 0:
                            st.session_state.debug_info.append(f"🖼️ Found {len(generated_images)} generated images")
                            print(f"DEBUG: Found {len(generated_images)} generated images")
                            print(f"DEBUG: First image object: {generated_images[0]}")
                            
                            # Try different possible URL fields
                            image_url = None
                            first_image = generated_images[0]
                            
                            if "url" in first_image:
                                image_url = first_image["url"]
                                st.session_state.debug_info.append(f"✅ Found URL in 'url' field")
                                print(f"DEBUG: Found URL in 'url' field: {image_url}")
                            elif "image_url" in first_image:
                                image_url = first_image["image_url"]
                                st.session_state.debug_info.append(f"✅ Found URL in 'image_url' field")
                                print(f"DEBUG: Found URL in 'image_url' field: {image_url}")
                            elif "imageUrl" in first_image:
                                image_url = first_image["imageUrl"]
                                st.session_state.debug_info.append(f"✅ Found URL in 'imageUrl' field")
                                print(f"DEBUG: Found URL in 'imageUrl' field: {image_url}")
                            else:
                                available_keys = list(first_image.keys())
                                st.session_state.debug_info.append(f"❌ No URL found. Available keys: {available_keys}")
                                print(f"DEBUG: No URL found in image object. Available keys: {available_keys}")
                            
                            if image_url:
                                st.session_state.debug_info.append(f"🎉 SUCCESS! Returning Leonardo AI image")
                                st.session_state.debug_info.append(f"📎 Image URL: {image_url}")
                                st.session_state.debug_info.append(f"🔍 URL Type: {type(image_url)}")
                                st.session_state.debug_info.append(f"📏 URL Length: {len(str(image_url))}")
                                print(f"DEBUG: Successfully returning Leonardo AI image: {image_url}")
                                return [image_url]
                            else:
                                st.session_state.debug_info.append("❌ No valid image URL found")
                                print("DEBUG: No valid image URL found")
                        else:
                            st.session_state.debug_info.append("❌ No generated images found in response")
                            print("DEBUG: No generated images found in response")
                    
                    # If this is the last attempt, break
                    if attempt == max_attempts - 1:
                        st.session_state.debug_info.append("⏰ Reached maximum polling attempts")
                        break
            else:
                st.session_state.debug_info.append("❌ No generation ID received from Leonardo AI")
        else:
            st.session_state.debug_info.append(f"❌ Leonardo AI API Error: {response.text}")
        
        # If Leonardo AI fails, return a sample image
        st.session_state.debug_info.append("🔄 Leonardo AI failed - using sample image as fallback")
        print("DEBUG: Leonardo AI failed - using sample image")
        return [SAMPLE_IMAGES[0]]
        
    except Exception as e:
        # Fallback to test mode
        st.session_state.debug_info.append(f"💥 Exception occurred: {str(e)}")
        print(f"DEBUG: Exception occurred: {e}")
        random.shuffle(SAMPLE_IMAGES)
        return [SAMPLE_IMAGES[0]]

def generate_song(genre):
    if APP_MODE == "test":
        time.sleep(6)  # Simulate generation delay
        return {
            "url": "https://example.com/generated-song.mp3",
            "title": f"{genre['name']} Anthem"
        }
    
    # Production mode - select from S3
    song_library = {
        'rock-anthem': [f"{S3_BUCKET_URL}/rock-anthem-{i}.mp3" for i in range(1, 5)],
        'electronic-hype': [f"{S3_BUCKET_URL}/electronic-hype-{i}.mp3" for i in range(1, 5)],
        'orchestral-epic': [f"{S3_BUCKET_URL}/orchestral-epic-{i}.mp3" for i in range(1, 5)],
        'inspirational-pop': [f"{S3_BUCKET_URL}/inspirational-pop-{i}.mp3" for i in range(1, 5)]
    }
    
    time.sleep(6)  # Simulate generation delay for dramatic effect
    genre_songs = song_library.get(genre['id'], [])
    selected_song = random.choice(genre_songs) if genre_songs else f"{S3_BUCKET_URL}/rock-anthem-1.mp3"
    
    return {
        "url": selected_song,
        "title": f"{genre['name']} Victory Anthem"
    }

# Authentication Page
def auth_page():
    st.markdown('<div class="main-header">🏆 Welcome</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Please enter passcode to access the KBS AI Demo</div>', unsafe_allow_html=True)
    
    with st.form("auth_form"):
        passcode = st.text_input("Access Passcode", type="password", placeholder="Enter passcode...")
        submit = st.form_submit_button("Access System", use_container_width=True)
        
        if submit:
            if passcode.upper() == "KBS2025":
                st.session_state.authenticated = True
                st.session_state.current_step = "loading" # Changed to loading state
                st.rerun()
            else:
                st.error("Invalid passcode. Please try again.")

# Loading Page
def loading_page():
    st.markdown('<div class="loading-container">', unsafe_allow_html=True)
    st.markdown('<div class="loading-spinner"></div>', unsafe_allow_html=True)
    st.markdown('<div class="loading-text">Authentication Successful! ✅</div>', unsafe_allow_html=True)
    st.markdown('<div class="loading-subtext">Initializing KBS AI Campaign Generator...</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-transition to input page after 2 seconds
    time.sleep(2)
    st.session_state.current_step = "input"
    st.rerun()

# Team Input Page
def team_input_page():
    st.markdown('<div class="main-header">🏆 AI Campaign Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Create customized marketing campaigns for your favourite sports team using AI</div>', unsafe_allow_html=True)
    
    with st.form("team_form"):
        team_name = st.text_input("Sports Team Name", placeholder="Enter your team's name...")
        submit = st.form_submit_button("Generate Campaign", use_container_width=True)
        
        if submit and team_name.strip():
            st.session_state.team_name = team_name.strip()
            st.session_state.current_step = "generating_briefs"
            st.rerun()

# Brief Generation Page
def brief_generation_page():
    st.markdown('<div class="main-header">📄 Generating Campaign Briefs...</div>', unsafe_allow_html=True)
    st.markdown('<div class="powered-by">Powered by OpenAI</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("OpenAI is crafting personalized campaign strategies...")
    
    # Generate both briefs
    briefs = []
    for i, brief_type in enumerate(["brief1", "brief2"]):
        progress_bar.progress((i + 1) * 50)
        brief_content = generate_brief(st.session_state.team_name, brief_type)
        briefs.append({
            "id": f"openai-brief-{i+1}",
            "content": brief_content,
            "source": "openai",
            "themes": ["Innovation", "Unity", "Resilience", "Championship"] if i == 1 else ["Legacy", "Community", "Excellence", "Passion"]
        })
    
    st.session_state.briefs = briefs
    st.session_state.current_step = "brief_selection"
    time.sleep(1)
    st.rerun()

# Brief Selection Page
def brief_selection_page():
    st.markdown('<div class="main-header">📄 Select Your Campaign Brief</div>', unsafe_allow_html=True)
    st.markdown('<div class="powered-by">Powered by OpenAI</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    for i, brief in enumerate(st.session_state.briefs):
        with col1 if i == 0 else col2:
            st.markdown(f"### ✨ OpenAI Strategy {i+1}")
            st.markdown(brief["content"])
            
            if st.button(f"Select Brief {i+1}", key=f"brief_{i}", use_container_width=True):
                st.session_state.selected_brief = brief
                st.session_state.current_step = "generating_images"
                st.rerun()

# Image Generation Page
def image_generation_page():
    st.markdown('<div class="main-header">🎨 Generating Campaign Image...</div>', unsafe_allow_html=True)
    st.markdown('<div class="powered-by">Powered by Leonardo AI</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text(f"Creating stunning visual for {st.session_state.team_name} using Leonardo AI...")
    
    # Generate images
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.30)  # 30 second total delay to match Leonardo AI generation time
    
    images = generate_images(st.session_state.selected_brief["content"], 1)
    st.session_state.images = [{"id": f"image-{i}", "url": url, "prompt": f"Campaign visual {i+1}"} for i, url in enumerate(images)]
    st.session_state.current_step = "image_selection"
    st.rerun()

# Image Selection Page  
def image_selection_page():
    st.markdown('<div class="main-header">🎨 Your Campaign Visual</div>', unsafe_allow_html=True)
    st.markdown('<div class="powered-by">Powered by Leonardo AI</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">AI-generated marketing visual for <strong>{st.session_state.team_name}</strong></div>', unsafe_allow_html=True)
    
    # Show debug info if available
    if st.session_state.debug_info:
        with st.expander("🔧 Generation Debug Info", expanded=False):
            for info in st.session_state.debug_info:
                st.write(info)
            
            # Check if this was a fallback to sample image
            if any("sample image as fallback" in info for info in st.session_state.debug_info):
                st.error("⚠️ Leonardo AI generation failed - showing sample image instead")
            elif any("TEST mode" in info for info in st.session_state.debug_info):
                st.info("ℹ️ Running in test mode - using sample images")
    
    # Since we only generate one image now, display it and auto-proceed
    if st.session_state.images and len(st.session_state.images) > 0:
        col1, col2, col3 = st.columns([0.5, 3, 0.5])
        with col2:
            try:
                image_url = st.session_state.images[0]["url"]
                
                # Debug: Show the URL we're trying to use
                if st.session_state.debug_info:
                    st.session_state.debug_info.append(f"🖼️ Attempting to display image URL: {image_url}")
                
                                 # Validate URL
                if image_url and isinstance(image_url, str) and len(image_url.strip()) > 0:
                    st.image(image_url, caption="Campaign Visual", use_column_width=True)
                else:
                    st.error("❌ Invalid image URL received from Leonardo AI")
                    st.write(f"URL received: {repr(image_url)}")
                    # Fallback to a sample image
                    st.image(SAMPLE_IMAGES[0], caption="Campaign Visual (Sample)", use_column_width=True)
                    
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
                st.write(f"Image URL: {repr(st.session_state.images[0].get('url', 'No URL'))}")
                # Fallback to a sample image
                st.image(SAMPLE_IMAGES[0], caption="Campaign Visual (Sample)", use_column_width=True)
        
        # Automatically select the single image
        st.session_state.selected_images = [st.session_state.images[0]]
        
        # Button columns for Continue and Regenerate
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Regenerate Image", use_container_width=True):
                st.session_state.current_step = "generating_images"
                st.rerun()
        
        with col2:
            if st.button("✅ Continue with This Visual", use_container_width=True):
                st.session_state.current_step = "genre_selection"
                st.rerun()
    else:
        st.error("No images were generated. Please try again.")
        if st.button("Go Back", use_container_width=True):
            st.session_state.current_step = "brief_selection"
            st.rerun()

# Genre Selection Page
def genre_selection_page():
    st.markdown('<div class="main-header">🎵 Choose Your Anthem Style</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Select the perfect musical genre for <strong>{st.session_state.team_name}</strong>\'s victory anthem</div>', unsafe_allow_html=True)
    st.markdown('<div class="powered-by">Powered by Suno AI</div>', unsafe_allow_html=True)
    
    cols = st.columns(2)
    
    for i, genre in enumerate(SONG_GENRES):
        with cols[i % 2]:
            if st.button(f"{genre['emoji']} {genre['name']}", key=f"genre_{i}", use_container_width=True):
                st.session_state.selected_genre = genre
                st.session_state.current_step = "generating_song"
                st.rerun()
            st.write(genre["description"])
            st.write("---")

# Song Generation Page
def song_generation_page():
    st.markdown('<div class="main-header">🎵 Generating Victory Anthem...</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Creating {st.session_state.selected_genre["name"]} for {st.session_state.team_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="powered-by">Powered by Suno AI</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Generating your custom victory anthem...")
    
    # Simulate song generation with progress
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.06)  # 6 second total delay
    
    song = generate_song(st.session_state.selected_genre)
    st.session_state.generated_song = song
    st.session_state.current_step = "complete"
    st.rerun()

# Final Campaign Page
def final_campaign_page():
    st.markdown('<div class="main-header">🏆 Campaign Complete!</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Your AI-powered marketing campaign for <strong>{st.session_state.team_name}</strong> is ready</div>', unsafe_allow_html=True)
    
    # Brief Section
    st.markdown("## 📄 Strategic Brief")
    st.markdown('<div class="powered-by">Powered by OpenAI</div>', unsafe_allow_html=True)
    st.markdown(st.session_state.selected_brief["content"])
    
    # Themes
    if st.session_state.selected_brief.get("themes"):
        st.write("**Campaign Themes:**")
        theme_cols = st.columns(len(st.session_state.selected_brief["themes"]))
        for i, theme in enumerate(st.session_state.selected_brief["themes"]):
            theme_cols[i].markdown(f"🏷️ **{theme}**")
    
    st.markdown("---")
    
    # Images Section
    st.markdown("## 🎨 Campaign Visual")
    st.markdown('<div class="powered-by">Powered by Leonardo AI</div>', unsafe_allow_html=True)
    
    # Display single image centered
    if st.session_state.selected_images and len(st.session_state.selected_images) > 0:
        col1, col2, col3 = st.columns([0.5, 3, 0.5])
        with col2:
            try:
                image_url = st.session_state.selected_images[0]["url"]
                if image_url and isinstance(image_url, str) and len(image_url.strip()) > 0:
                    st.image(image_url, caption="Campaign Visual", use_column_width=True)
                else:
                    st.error("❌ Invalid image URL")
                    st.image(SAMPLE_IMAGES[0], caption="Campaign Visual (Sample)", use_column_width=True)
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
                st.image(SAMPLE_IMAGES[0], caption="Campaign Visual (Sample)", use_column_width=True)
    
    st.markdown("---")
    
    # Song Section
    st.markdown("## 🎵 Victory Anthem")
    st.markdown('<div class="powered-by">Powered by Suno AI</div>', unsafe_allow_html=True)
    if st.session_state.generated_song:
        st.markdown(f"### 🎼 {st.session_state.generated_song['title']}")
        st.markdown(f"**Genre:** {st.session_state.selected_genre['name']}")
        st.markdown(f"**Style:** {st.session_state.selected_genre['description']}")
        
        # Real audio player with S3 files
        if st.session_state.generated_song.get("url"):
            song_url = st.session_state.generated_song["url"]
            
            # Try to load the audio file
            try:
                st.audio(song_url, format="audio/mp3")
                st.markdown(f"🎵 **Now Playing:** {st.session_state.generated_song['title']}")
            except Exception as e:
                # If S3 files aren't accessible, show a demo message
                st.warning("🎵 Audio files are currently being configured for public access")
                st.info(f"**Selected Track:** {st.session_state.generated_song['title']}")
                st.markdown(f"**Genre:** {st.session_state.selected_genre['name']}")
                st.markdown("*In the full production version, this would play the actual victory anthem*")
        else:
            st.info("🎵 Audio file not available")
    
    st.markdown("---")
    
    # Success message
    st.markdown('<div class="success-message">✅ Victory Anthem Generated! Your custom victory anthem is ready</div>', unsafe_allow_html=True)
    
    # New Campaign Button
    if st.button("🔄 Create New Campaign", use_container_width=True):
        # Reset campaign data but keep authentication
        for key in ['team_name', 'briefs', 'selected_brief', 'images', 'selected_images', 'selected_genre', 'generated_song']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Ensure we stay authenticated and go to team input page
        st.session_state.authenticated = True
        st.session_state.current_step = "input"
        st.rerun()

# Main App Logic
def main():
    if not st.session_state.authenticated:
        auth_page()
    elif st.session_state.current_step == "loading":
        loading_page()
    elif st.session_state.current_step == "input":
        team_input_page()
    elif st.session_state.current_step == "generating_briefs":
        brief_generation_page()
    elif st.session_state.current_step == "brief_selection":
        brief_selection_page()
    elif st.session_state.current_step == "generating_images":
        image_generation_page()
    elif st.session_state.current_step == "image_selection":
        image_selection_page()
    elif st.session_state.current_step == "genre_selection":
        genre_selection_page()
    elif st.session_state.current_step == "generating_song":
        song_generation_page()
    elif st.session_state.current_step == "complete":
        final_campaign_page()

if __name__ == "__main__":
    main() 