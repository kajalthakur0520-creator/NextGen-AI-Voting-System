import os, glob, re

template_dir = 'c:\\Users\\HP\\OneDrive\\Desktop\\-Web-Based-Biometric-Voting-System--main\\templates'
files = glob.glob(os.path.join(template_dir, '*.html'))

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Nav wrapper replacement
    new_content = re.sub(
        r'<nav class="glass-nav py-(\d+) px-8 relative z-10 flex justify-between items-center">',
        r'<nav class="glass-nav py-\1 px-4 md:px-8 relative z-10 flex flex-col md:flex-row justify-between items-center gap-4">',
        content
    )
    
    # Internal div links container replacement
    new_content = re.sub(
        r'<div class="flex gap-(\d+) items-center">',
        r'<div class="flex flex-wrap justify-center gap-\1 items-center">',
        new_content
    )
    
    # Internal div for index which has more classes
    new_content = re.sub(
        r'<div class="flex gap-(\d+) text-sm font-medium tracking-wide items-center">',
        r'<div class="flex flex-wrap gap-\1 text-sm font-medium tracking-wide items-center justify-center">',
        new_content
    )

    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')
