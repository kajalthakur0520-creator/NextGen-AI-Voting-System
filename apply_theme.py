import os
import glob
import re

TEMPLATE_DIR = r"c:\Users\bella\Desktop\-Web-Based-Biometric-Voting-System--main\templates"

NEW_STYLE = """    <style>
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            overflow-x: hidden;
            background-color: #0f172a;
            color: #f8fafc;
        }
        
        .bg-gif-layer {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: url('https://media.giphy.com/media/3o7aD2d7xc9vP8Vg1a/giphy.gif') no-repeat center center fixed;
            background-size: cover;
            z-index: -3;
            opacity: 0.6;
            filter: saturate(1.5) contrast(1.2);
        }

        .bg-gradient-layer {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(
                -45deg, 
                rgba(236, 72, 153, 0.5), /* Pink */
                rgba(139, 92, 246, 0.4), /* Violet */
                rgba(56, 189, 248, 0.4), /* Cyan */
                rgba(52, 211, 153, 0.4)  /* Emerald */
            );
            background-size: 400% 400%;
            animation: moveGradient 15s ease infinite;
            z-index: -2;
            mix-blend-mode: overlay;
        }
        
        @keyframes moveGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .dark-dim-layer {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(15, 23, 42, 0.7);
            z-index: -1;
        }

        h1, h2, h3, h4, th, .heading-font {
            font-family: 'Poppins', sans-serif;
        }
        
        .glass-nav {
            background: rgba(15, 23, 42, 0.4);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        .glass-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
            backdrop-filter: blur(28px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4), inset 0 0 1px rgba(255, 255, 255, 0.3);
            border-top: 1px solid rgba(255, 255, 255, 0.4);
            border-left: 1px solid rgba(255, 255, 255, 0.3);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .glass-card::before {
            content: '';
            position: absolute;
            top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent);
            transform: skewX(-20deg);
            transition: all 0.7s ease;
        }
        
        .glass-card:hover::before {
            left: 200%;
        }

        .glass-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 35px 60px rgba(0, 0, 0, 0.5), inset 0 0 2px rgba(255, 255, 255, 0.4), 0 0 40px rgba(139, 92, 246, 0.3);
            border-color: rgba(236, 72, 153, 0.3);
        }

        .gradient-text {
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 30%, #f093fb 70%, #f5576c 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            background-size: 200% auto;
            animation: shineText 4s linear infinite;
        }
        
        @keyframes shineText {
            to { background-position: 200% center; }
        }
        
        .floating-element {
            animation: float 6s ease-in-out infinite;
        }
        
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
            100% { transform: translateY(0px); }
        }

        .btn-elegant {
            background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
            border: none;
            position: relative;
            z-index: 1;
            overflow: hidden;
            transition: all 0.4s ease;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);
        }
        
        .btn-elegant::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
            z-index: -1;
            transition: opacity 0.4s ease;
            opacity: 0;
        }
        
        .btn-elegant:hover::before {
            opacity: 1;
        }
        
        .btn-elegant:hover {
            box-shadow: 0 0 25px rgba(240, 147, 251, 0.7);
            transform: translateY(-3px) scale(1.02);
        }
        
        .btn-outline {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(10px);
            transition: all 0.4s ease;
        }
        
        .btn-outline:hover {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(236, 72, 153, 0.6);
            box-shadow: 0 0 20px rgba(236, 72, 153, 0.4);
            transform: translateY(-3px);
        }
        
        .glass-input {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            transition: all 0.3s ease;
        }
        
        .glass-input:focus {
            outline: none;
            border-color: rgba(240, 147, 251, 0.8);
            background: rgba(15, 23, 42, 0.7);
            box-shadow: 0 0 20px rgba(240, 147, 251, 0.4);
            transform: scale(1.01);
        }
        
        .pulse-border {
            animation: borderPulse 3s infinite;
        }
        
        @keyframes borderPulse {
            0% { border-color: rgba(255,255,255,0.1); }
            50% { border-color: rgba(240, 147, 251, 0.6); box-shadow: 0 0 20px rgba(240, 147, 251, 0.3); }
            100% { border-color: rgba(255,255,255,0.1); }
        }
    </style>"""

NEW_OVERLAYS = """    <!-- Background Animation Elements -->
    <div class="bg-gif-layer"></div>
    <div class="bg-gradient-layer"></div>
    <div class="dark-dim-layer"></div>"""

for html_file in glob.glob(os.path.join(TEMPLATE_DIR, "*.html")):
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Replace style block. Use regex that works across multiple lines.
    content = re.sub(r"    <style>.*?</style>", NEW_STYLE, content, flags=re.DOTALL)
    
    # 2. Replace old dark overlays with the new layered backgrounds.
    # Try different known overlay patterns
    content = re.sub(r'    <!-- Dark overlay -->.*?    <div class="fixed inset-0 bg-slate-950/.*?></div>', NEW_OVERLAYS, content, flags=re.DOTALL)
    content = re.sub(r'    <!-- Elegant dark overlay for contract -->.*?    <div class="fixed inset-0 bg-slate-950/.*?></div>', NEW_OVERLAYS, content, flags=re.DOTALL)
    content = re.sub(r'    <div class="fixed inset-0 bg-slate-950/70.*?div>', NEW_OVERLAYS, content, flags=re.DOTALL)
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Update applied to all HTML templates in {TEMPLATE_DIR}")
