import os
import glob

TEMPLATE_DIR = r"c:\Users\bella\Desktop\-Web-Based-Biometric-Voting-System--main\templates"
OLD_GIF = "https://media.giphy.com/media/3o7aD2d7xc9vP8Vg1a/giphy.gif"
NEW_GIF = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExZWZkam8wcnFjN2c1Mmk0eDR1bzE3dHh6bHg3Z3llZ3NpNmZxdDJoNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YqhIK6Gbor6CLeloBq/giphy.gif"

count = 0
for html_file in glob.glob(os.path.join(TEMPLATE_DIR, "*.html")):
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    if OLD_GIF in content:
        content = content.replace(OLD_GIF, NEW_GIF)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1

print(f"Successfully replaced GIF in {count} HTML files.")
