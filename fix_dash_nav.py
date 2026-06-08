import os, re

files = ['voter_dashboard.html', 'voter_complaint.html', 'vote.html', 'candidate_dashboard.html']
template_dir = 'c:\\Users\\HP\\OneDrive\\Desktop\\-Web-Based-Biometric-Voting-System--main\\templates'

for f in files:
    path = os.path.join(template_dir, f)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace the flex container for nav items
        content = re.sub(
            r'class="max-w-(\w+) mx-auto flex justify-between items-center"',
            r'class="max-w-\1 mx-auto flex flex-col md:flex-row justify-between items-center gap-4"',
            content
        )
        content = re.sub(
            r'class="max-w-(\w+) mx-auto flex items-center justify-between"',
            r'class="max-w-\1 mx-auto flex flex-col md:flex-row items-center justify-between gap-4"',
            content
        )
        
        # Replace the inner div wrapping the links
        content = re.sub(
            r'class="flex items-center space-x-4"',
            r'class="flex flex-wrap items-center justify-center space-x-2 md:space-x-4"',
            content
        )
        content = re.sub(
            r'class="flex items-center space-x-6"',
            r'class="flex flex-wrap items-center justify-center space-x-2 md:space-x-6"',
            content
        )

        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Updated {f}')
