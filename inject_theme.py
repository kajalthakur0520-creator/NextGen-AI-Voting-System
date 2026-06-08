import os
import glob
import re

TEMPLATE_DIR = r"c:\Users\bella\Desktop\-Web-Based-Biometric-Voting-System--main\templates"

LINK_TAG = """    <link rel="stylesheet" href="{{ url_for('static', filename='css/theme.css') }}">
    <script src="{{ url_for('static', filename='js/theme.js') }}"></script>
"""

count = 0
for html_file in glob.glob(os.path.join(TEMPLATE_DIR, "*.html")):
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if already injected
    if "theme.css" in content:
        continue
        
    # Inject before </head>
    if "</head>" in content:
        content = content.replace("</head>", LINK_TAG + "</head>")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1

print(f"Theme injected into {count} HTML templates.")
