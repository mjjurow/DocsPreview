import requests
from urllib.parse import urlparse
import base64
from bs4 import BeautifulSoup
import markdown
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

def get_readme_start(request):
    owner = str(request.args.get('User', None))
    repo = str(request.args.get('Repo', None))
    
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(readme_url)
    
    if response.status_code == 200:
        readme_content_base64 = response.json()['content']
        readme_content = base64.b64decode(readme_content_base64).decode('utf-8')
        
        # Convert markdown to HTML
        html_content = markdown.markdown(readme_content)
        
        # Convert HTML to plain text
        soup = BeautifulSoup(html_content, "html.parser")
        plain_text = soup.get_text()
        
        # Filter out lines that still seem non-informative:
        filtered_lines = [line for line in plain_text.split("\n") if line and not line.startswith(('http', '#'))]
        filtered_text = "\n".join(filtered_lines[:150])  # only taking first 150 lines

        return filtered_text
    else:
        return None

def split_text_into_chunks(text, max_tokens=500):  # 500 is an example value; adjust as needed
    lines = text.split('\n')
    chunks = []
    current_chunk = ''
    current_token_count = 0
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2-medium")
    for line in lines:
        line_token_count = len(tokenizer.encode(line))
        if current_token_count + line_token_count < max_tokens:
            current_chunk += line + '\n'
            current_token_count += line_token_count
        else:
            chunks.append(current_chunk)
            current_chunk = line + '\n'
            current_token_count = line_token_count
    
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def how_many_tokens(text):
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2-large")
    tokenized_text = tokenizer.encode(text)
    token_count = len(tokenized_text)
    return token_count

def summarize(text):
    tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")#google/pegasus-xsum / facebook/bart-large-cnn / csebuetnlp/mT5_multilingual_XLSum 
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")

    tokens_input = tokenizer.encode("summarize: "+ long_readme, return_tensors='pt', max_length=512, truncation=True)
    ids = model.generate(tokens_input, min_length=80, max_length=120)
    summary = tokenizer.decode(ids[0], skip_special_tokens=True)

    return summary