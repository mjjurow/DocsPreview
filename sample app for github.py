from typing import Any, Mapping
import requests
import flask
import functions_framework
import json
import google.cloud.logging
import logging
from urllib.parse import urlparse

BASE_URL = #CLOUDFUNCTION
BASE_GIT_URL = #GITHUB

# Logging setup
client = google.cloud.logging.Client()
client.setup_logging()
logging.warning('logging is active')

@functions_framework.http
def create_link_preview(req): 
    event = req.get_json(silent=True)
    function_name = req.args.get('function')

    logging.warning('create_link_preview called')
    
    function_handlers = {
        'Stack_Q': Stack_Q,
        'Stack_Best_A': Stack_Best_A,
        'Stack_2nd_A': Stack_2nd_A,
        'Github_Card': Github_Card,
        'Github_Repository_Card': Github_Repository_Card,
        'Github_ListOfPullRequests_Card': Github_ListOfPullRequests_Card,
        'Github_ListOfIssues_Card': Github_ListOfIssues_Card,
        'Github_User_Card': Github_User_Card,
        'Github_PullRequest_Card': Github_PullRequest_Card,
        'Github_Issue_Card': Github_Issue_Card,
        'Github_Repository_Card_Update': Github_Repository_Card_Update,
        'Github_ListOfPullRequests_Card_Update': Github_ListOfPullRequests_Card_Update,
        'Github_ListOfIssues_Card_Update': Github_ListOfIssues_Card_Update,
        'Summarize': Summarize
        }

    if function_name in function_handlers:
        logging.warning('create_link_preview called with '+ str(function_name))
        return function_handlers[function_name](req)    
    
    if event is not None:
        try:
            url = event["docs"]["matchedUrl"]["url"]
            logging.warning('create_link_preview called with event string: return call_card(url)')
            return call_card(url)
        except KeyError as e:
            logging.error(f"JSON doesn't contain expected fields: {str(e)}")
            return f"JSON doesn't contain expected fields: {str(e)}"
    else:
        logging.error('No JSON received')
        return 'No JSON received'

def call_card(url): 
    parsed_url = urlparse(url)     
    logging.info('inside call_card with' + str(parsed_url))

    if parsed_url.hostname.startswith("stackoverflow"): 
        logging.warning('returning stack_card with ' + str(parsed_url.path))
        return Stack_Card(parsed_url.path)

    elif "github.com" in parsed_url.hostname:
        logging.warning('returning github_card with ' + str(parsed_url.path))
        return Github_Card(parsed_url.path)
    
    else:
        return Blank_Card(url)  

def fetch_stackexchange_data(url, params):
    response = requests.get(url, params = params)
    return response.json()

def create_card(widgets,buttons):
    return { 
        "renderActions": {
            "action": {
                "navigations": [
                    {
                        "updateCard": {
                            "sections": [
                                {
                                    "widgets": widgets + [
                                        {
                                            "buttonList": {
                                                "buttons": buttons
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }

def Stack_Card(parsed_path):
    Card_Text = parsed_path.split('/')[3].replace('-',' ').title() #the question in title case
    Stack_ID_string = str(parsed_path.split('/')[2])
    
    question_url = f"https://api.stackexchange.com/2.3/questions/{Stack_ID_string}"
    question_params = {
        "site": "stackoverflow",
        "filter": "withbody"
        }
    
    question_data = fetch_stackexchange_data(question_url, question_params)

    question_body = question_data["items"][0]["body"].replace('<p>', ' ').replace('</p>', ' ') 
    question_upvotes = question_data["items"][0]["score"] 
    q_score_str = str("Score: " + str(question_upvotes))
    
    Best_Answer_URL = f"{BASE_URL}?function=Stack_Best_A&Stack_ID_string={Stack_ID_string}"
    Second_Answer_URL = f"{BASE_URL}?function=Stack_2nd_A&Stack_ID_string={Stack_ID_string}"

    return {
    "action": {
    "linkPreview": {
      "title": Card_Text,
      "linkPreviewTitle": "Stack Exchange Question",
      "previewCard": {  
        "sections": [
          {
            "widgets": [
                {"decoratedText":{
            "topLabel": Card_Text}},
            {"textParagraph": {"text": question_body}},
            {"textParagraph": {"text": q_score_str}},
              {
                "buttonList": {
                  "buttons": [
                    {"text": "Best Answer","onClick": {"action": {"function": Best_Answer_URL}}},
                    {"text": "2nd Answer","onClick": {"action": {"function": Second_Answer_URL}}}]
                  }}]}]}}}}

def Blank_Card(url):
    urlstring = str(url)
    logging.info('Blank Card from ' + urlstring)
    return {
    "action": {
    "linkPreview": {
      "title": "smart chip title",
      "linkPreviewTitle": "Blank Card",
      "previewCard": {
        "header": {
          "title": "Something terrible has happened."
        },
        "sections": [
          {
            "widgets": [
              {
                "textParagraph": {
                  "text": urlstring 
                }
              }
            ]
          }
        ]
      }
    }
  }
}

def stack_url_with_function(function,Stack_ID_string):
    return f"{BASE_URL}?function={function}&Stack_ID_string={Stack_ID_string}"

def Stack_Best_A(request):
    Stack_ID_string = str(request.args.get('Stack_ID_string', None))
    
    if not Stack_ID_string:
        logging.error('no Stack ID string best answer')
        return
    
    answer_url = f"https://api.stackexchange.com/2.3/questions/{Stack_ID_string}/answers"
    params = {
        "site": "stackoverflow",
        "order": "desc",
        "sort": "votes",
        "filter": "withbody"
    }
    answer_data = fetch_stackexchange_data(answer_url, params)

    first_answer = answer_data["items"][0]["body"].replace('<p>', ' ').replace('<strong>', ' ').replace('</strong>', ' ').replace('</p>', '\n')
    first_answer_votes = answer_data["items"][0]["score"]
    A_score_str = str("Score: " + str(first_answer_votes))

    widgets = [
        {"textParagraph": {"text": first_answer}},
        {"textParagraph": {"text": A_score_str}}
    ]

    buttons = [
        {
            "text": "Question",
            "onClick": {"action": {"function": stack_url_with_function("Stack_Q", Stack_ID_string)}}
        },
        {
            "text": "2nd Answer",
            "onClick": {"action": {"function": stack_url_with_function("Stack_2nd_A", Stack_ID_string)}}
        }
    ]

    return create_card(widgets, buttons)

def Stack_2nd_A(request):
    
    Stack_ID_string = str(request.args.get('Stack_ID_string', None))

    if not Stack_ID_string:
        logging.error('no Stack ID string for 2nd answer')
        return

    answer_url = f"https://api.stackexchange.com/2.3/questions/{Stack_ID_string}/answers"
    params = {
        "site": "stackoverflow",
        "order": "desc",
        "sort": "votes",
        "filter": "withbody"
    }
    answer_data = fetch_stackexchange_data(answer_url, params)

    if "items" not in answer_data or len(answer_data["items"]) < 2:
        return {"error": "Not enough answers available"}

    second_answer = answer_data["items"][1]["body"]
    second_answer = second_answer.replace('<p>', ' ').replace('<strong>', ' ').replace('</strong>', ' ').replace('</p>', '\n')
    second_answer_votes = str(answer_data["items"][1]["score"])
    A2_score_str = str('Score: ' + second_answer_votes)

    widgets = [
        {"textParagraph": {"text": second_answer}},
        {"textParagraph": {"text": A2_score_str}}
    ]

    buttons = [
        {
            "text": "Question",
            "onClick": {"action": {"function": stack_url_with_function("Stack_Q", Stack_ID_string)}}
        },
        {
            "text": "Best Answer",
            "onClick": {"action": {"function": stack_url_with_function("Stack_Best_A", Stack_ID_string)}}
        }
    ]
    return create_card(widgets, buttons)

def Stack_Q(request): 
    Stack_ID_string = str(request.args.get('Stack_ID_string', None))
    
    if not Stack_ID_string:
        logging.error('no Stack ID string question')
        return

    question_url = f"https://api.stackexchange.com/2.3/questions/{Stack_ID_string}"
    question_params = {
        "site": "stackoverflow",
        "filter": "withbody"
        }
    
    question_data = fetch_stackexchange_data(question_url, question_params)

    question_body = question_data["items"][0]["body"].replace('<p>', ' ').replace('</p>', ' ') 
    question_upvotes = question_data["items"][0]["score"] 
    q_score_str = str("Score: " + str(question_upvotes))

    widgets = [
        {"textParagraph": {"text": question_body}},
        {"textParagraph": {"text": q_score_str}}
    ]

    buttons = [
        {
            "text": "Best Answer",
            "onClick": {"action": {"function": stack_url_with_function("Stack_Best_A", Stack_ID_string)}}
        },
        {
            "text": "2nd Answer",
            "onClick": {"action": {"function": stack_url_with_function("Stack_2nd_A", Stack_ID_string)}}
        }
    ]
    return create_card(widgets, buttons)

def Github_Card(parsed_path):
    parts = parsed_path.split('/')
    parts = [part for part in parts if part]

    # User profile page
    if len(parts) == 1:
        return Github_User_Card(parts[0])

    # Repository main page
    elif len(parts) == 2:
        user = parts[0]
        repo = parts[1]
        return Github_Repository_Card(user, repo)

    # Issues or Pull Requests list or specific issue/pull request
    elif len(parts) == 3:
        user = parts[0]
        repo = parts[1]
        
        if parts[2] == "issues":
            return Github_ListOfIssues_Card(user, repo)
            
        elif parts[2] == "pulls":
            return Github_ListOfPullRequests_Card(user, repo)
        
        elif parts[0] == "orgs":
            user = parts[1]
            return Github_All_Repos(user)

    elif len(parts) == 4:
        user = parts[0]
        repo = parts[1]
        
        if parts[2] == "issues":
            issue_number = parts[3]
            return Github_Issue_Card(user, repo, issue_number)
            
        elif parts[2] == "pull":
            pr_number = parts[3]
            return Github_PullRequest_Card(user, repo, pr_number)

    logging.warning('something bad in github_card')
    return Blank_Card(parsed_path)

def Github_Repository_Card(user, repo):
    repo_info_url = f"{BASE_GIT_URL}/repos/{user}/{repo}"
    headers = {'User-Agent': 'request'}

    repo_info = requests.get(repo_info_url, headers=headers).json()

    Pull_Requests_URL = f"{BASE_URL}?function=Github_ListOfPullRequests_Card_Update&User={user}&Repo={repo}"
    Issues_Page_URL = f"{BASE_URL}?function=Github_ListOfIssues_Card_Update&User={user}&Repo={repo}"
    Summarize_URL = f"{BASE_URL}?function=Summarize&User={user}&Repo={repo}"
    
    Repository_Name = repo_info['name']
    Star_Count= 'Stars: ' + str(repo_info['stargazers_count'])
    Owner_name = f"Owner Name: {user}"
    License_info = f"License: {repo_info['license']['name'] if repo_info['license'] else 'No License Specified'}"

    Readme_Link= f"https://github.com/{user}/{repo}/blob/master/README.md"    

    Card_Type = f"GitHub Repository: {Repository_Name}"
  

    return {
    "action": {
    "linkPreview": {
      "title": Card_Type,
      "linkPreviewTitle": "GitHub Repository",
      "previewCard": {
        "sections": [
        {
          "widgets": [
              {"decoratedText":{
          "topLabel": Repository_Name}},
        {"textParagraph": {"text": Star_Count}},
        {"textParagraph": {"text": Owner_name}},
        {"textParagraph": {"text": License_info}},
            {
              "buttonList": {
                "buttons": [
                    {"text": "Pull Requests", "onClick": {"action": {"function": Pull_Requests_URL}}},
                    {"text": "All Issues", "onClick": {"action": {"function": Issues_Page_URL}}},
                    {"text": "View ReadMe", "onClick": {"openLink": {"url": Readme_Link}}},
                    {"text": "Summarize ReadMe", "onClick": {"action": {"function": Summarize_URL}}}
                  ]}}]}]}}}}
        
def Github_ListOfPullRequests_Card(user, repo):
    headers = {'User-Agent': 'request'}

    pulls_url = f"{BASE_GIT_URL}/repos/{user}/{repo}/pulls"
    repo_info_url = f"{BASE_GIT_URL}/repos/{user}/{repo}"
    repo_info = requests.get(repo_info_url, headers=headers).json()
    
    response = requests.get(pulls_url, headers=headers, params={'per_page': 5, 'state': 'all'}).json()

    First_five_pulls = "First Five Pull Requests: \n"

    for pull in response:
        First_five_pulls += (f"Pull Request Title: {pull['title']}\n")
        First_five_pulls += (f"Pull Request Status: {pull['state']}\n")
        First_five_pulls += ("-----\n")

    Card_Type = "List of Pull Requests"
    
    Repo_URL = f"{BASE_URL}?function=Github_Repository_Card_Update&User={user}&Repo={repo}"
    
    Repository_Name = repo_info['name']
    Owner_name = f"Owner Name: {user}"

    return {
    "action": {
    "linkPreview": {
      "title": f"{Card_Type}: {Repository_Name}",
      "linkPreviewTitle": Card_Type,
      "previewCard": {
        "sections": [
          {
            "widgets": [
                {"decoratedText":{"topLabel": f"Repository Name: {Repository_Name}"}},
        {"textParagraph": {"text": Owner_name}},
        {"textParagraph": {"text": First_five_pulls}},
              {
                "buttonList": {
                  "buttons": [
                    {"text": "Parent Repository", "onClick": {"action": {"function": Repo_URL}}}
                  ]}}]}]}}}}

def Github_ListOfIssues_Card(user, repo):
    
    headers = {'User-Agent': 'request'}
    issues_url = f"{BASE_GIT_URL}/repos/{user}/{repo}/issues"
    repo_info_url = f"{BASE_GIT_URL}/repos/{user}/{repo}"
    repo_info = requests.get(repo_info_url, headers=headers).json()    
    
    
    response = requests.get(issues_url, headers=headers, params={'per_page': 5, 'state': 'all'}).json()

    First_five_issues = "First Five Issues: \n"

    for issue in response:
        First_five_issues += (f"Issue Title: {issue['title']}\n")
        First_five_issues += (f"Issue Status: {issue['state']}\n")
        First_five_issues += ("-----\n")

    Card_Type = "List of Issues"
    
    Repo_URL = f"{BASE_URL}?function=Github_Repository_Card_Update&User={user}&Repo={repo}"

    Repository_Name = repo_info['name']
    Owner_name = f"Owner Name: {user}"

    return {
    "action": {
    "linkPreview": {
      "title": f"{Card_Type}: {Repository_Name}",
      "linkPreviewTitle": Card_Type,
      "previewCard": {
        "sections": [
          {
            "widgets": [
                {"decoratedText":{"topLabel": f"Repository Name: {Repository_Name}"}},
        {"textParagraph": {"text": Owner_name}},
        {"textParagraph": {"text": First_five_issues}},
              {
                "buttonList": {
                  "buttons": [
                    {"text": "Parent Repository", "onClick": {"action": {"function": Repo_URL}}}
                  ]}}]}]}}}}

def Github_User_Card(user):

    user_info_url = f"{BASE_GIT_URL}/users/{user}"
    headers = {'User-Agent': 'request'}
    user_repos_url = f"{BASE_GIT_URL}/users/{user}/repos"

    user_info = requests.get(user_info_url, headers=headers).json()
    user_repos = requests.get(user_repos_url, headers=headers).json()
    
    star_count = sum([repo['stargazers_count'] for repo in user_repos])
    top_repos = sorted(user_repos, key=lambda repo: repo['stargazers_count'], reverse=True)[:5]
    popular_repos = "Top Repositories: \n" 
    for repo in top_repos:
        popular_repos += f"{repo['stargazers_count']} stars: {repo['name']}\n"
    
    Owner_name = f"Owner Name: {user}"

    No_follows = f"Number of Followers: {user_info['followers']}"
    No_following = f"Number Following: {user_info['following']}"
    Tot_star= f"Total Stars on Repositories: {star_count}"

    return {
    "action": {
    "linkPreview": {
      "title": f"GitHub: {user}",
      "linkPreviewTitle": "GitHub User Page",
      "previewCard": {
        "sections": [
          {
            "widgets": [
                {"decoratedText":{"topLabel": f"GitHub: {user}"}},
        {"textParagraph": {"text": Owner_name}},
        {"textParagraph": {"text": No_follows}},
        {"textParagraph": {"text": No_following}},
        {"textParagraph": {"text": Tot_star}},
        {"textParagraph": {"text": popular_repos}}
                  ]}]}}}}

def Github_PullRequest_Card(user, repo, pr_number):
    pr_url = f"https://api.github.com/repos/{user}/{repo}/pulls/{pr_number}"
    headers = {'User-Agent': 'request'}
    pr_info = requests.get(pr_url, headers=headers).json()
    
    Title = f"Title: {pr_info['title']}\n"
    JustTitle = pr_info['title']
    Labels = f"Labels: {', '.join([label['name'] for label in pr_info['labels']]) or 'None'}\n"
    State = f"State: {pr_info['state']}\n" 
    CreatedBy = f"Created by: {pr_info['user']['login']}\n"
    Comments = f"Number of comments: {pr_info['comments']}\n\n"
    Commits = f"Number of commits: {pr_info['commits']}\n"
    Additions = f"Number of additions: {pr_info['additions']}\n"
    Deletions = f"Number of deletions: {pr_info['deletions']}\n\n"
    CreatedAt = f"Created Date/Time: {pr_info['created_at']}\n"
    ClosedAt = f"Closed Date/Time: {pr_info['closed_at'] or 'Not closed'}\n\n"
    OriginBranch = f"Originating branch: {pr_info['head']['label']}\n"
    TargetBranch = f"Target branch: {pr_info['base']['label']}\n\n"
    Mergeable = f"Mergeable state: {'Yes' if pr_info['mergeable'] else 'No'}\n"
    ReviewStatus = f"Review status: {pr_info['mergeable_state']}\n\n"  
    Body = f"Body: {pr_info['body']}"
    reponame = f"Parent Repository: {repo}\n\n"

    Full_Text = Title+reponame+Labels+State+CreatedBy+Comments+Commits+Additions+Deletions+CreatedAt+ClosedAt+OriginBranch+TargetBranch+Mergeable+ReviewStatus+Body
    
    Repo_link = f"https://github.com/{user}/{repo}/" 
    

    return {
    "action": {
    "linkPreview": {
    "title": f"Pull Request: {JustTitle}",
    "linkPreviewTitle": "GitHub: Pull Request",
    "previewCard": {  
      "sections": [
        {
          "widgets": [
              {"decoratedText":{
          "topLabel": f"Pull Request: {JustTitle}"}},
          {"textParagraph": {"text": Full_Text}},
            {
              "buttonList": {
                "buttons": [
                  {"text": "Parent Repository", "onClick": {"openLink": {"url": Repo_link}}}]
                }}]}]}}}}
    
def Github_Issue_Card(user, repo, issue_number):

    issue_url = f"https://api.github.com/repos/{user}/{repo}/issues/{issue_number}"
    headers = {'User-Agent': 'request'}
    issue_info = requests.get(issue_url, headers=headers).json()
    
    Repo_link = f"https://github.com/{user}/{repo}/"

    Title = f"Title: {issue_info['title']}\n"
    JustTitle = issue_info['title']
    Repo_URL = f"Repository URL: https://github.com/{user}/{repo}\n\n"
    Labels = f"Labels: {', '.join([label['name'] for label in issue_info['labels']]) or 'None'}"
    State = f"\nState: {issue_info['state']}\n\n"
    Created_by = f"Created by: {issue_info['user']['login']}\n"
    Assignees = f"Assignees: {', '.join([assignee['login'] for assignee in issue_info['assignees']]) or 'None'}\n"
    Created_date = f"Created Date/Time: {issue_info['created_at']}\n"
    Closed_date = f"Closed Date/Time: {issue_info['closed_at'] or 'Not closed'}\n--------\n\n"
    Body = f"Body: {issue_info['body']}"
    
    Full_Text = Title+Repo_URL+Labels+State+Created_by+Assignees+Created_date+Closed_date+Body
    
    return {
    "action": {
    "linkPreview": {
    "title": f"Pull Request: {JustTitle}",
    "linkPreviewTitle": "GitHub: Issue",
    "previewCard": {  
      "sections": [
        {
          "widgets": [
              {"decoratedText":{
          "topLabel": f"Issue: {JustTitle}"}},
          {"textParagraph": {"text": Full_Text}},
            {
              "buttonList": {
                "buttons": [
                  {"text": "Parent Repository", "onClick": {"openLink": {"url": Repo_link}}}]
                }}]}]}}}}

def Github_Repository_Card_Update(request):
    
    user = str(request.args.get('User', None))
    repo = str(request.args.get('Repo', None))
    
    repo_info_url = f"{BASE_GIT_URL}/repos/{user}/{repo}"
    headers = {'User-Agent': 'request'}
    
    repo_info = requests.get(repo_info_url, headers=headers).json()

    Pull_Requests_URL = f"{BASE_URL}?function=Github_ListOfPullRequests_Card_Update&User={user}&Repo={repo}"
    Issues_Page_URL = f"{BASE_URL}?function=Github_ListOfIssues_Card_Update&User={user}&Repo={repo}"
    Summarize_URL = f"{BASE_URL}?function=Summarize&User={user}&Repo={repo}"
    
    Repository_Name = repo_info['name']
    Star_Count= 'Stars: ' + str(repo_info['stargazers_count'])
    Owner_name = f"Owner Name: {user}"
    License_info = f"License: {repo_info['license']['name'] if repo_info['license'] else 'No License Specified'}"
    Readme_Link= f"https://github.com/{user}/{repo}/blob/master/README.md"     

    returncard = {
        "sections": [
        {
          "widgets": [
              {"decoratedText":{
          "topLabel": Repository_Name}},
        {"textParagraph": {"text": Star_Count}},
        {"textParagraph": {"text": Owner_name}},
        {"textParagraph": {"text": License_info}},
            {
              "buttonList": {
                "buttons": [
                    {"text": "Pull Requests", "onClick": {"action": {"function": Pull_Requests_URL}}},
                    {"text": "All Issues", "onClick": {"action": {"function": Issues_Page_URL}}},
                    {"text": "View ReadMe", "onClick": {"openLink": {"url": Readme_Link}}},
                    {"text": "Summarize ReadMe", "onClick": {"action": {"function": Summarize_URL}}}
                  ]}}]}]}

    return { 
        "renderActions": {
            "action": {
                "navigations": [
                    {
                        "pushCard": returncard}]}}}

def Github_ListOfPullRequests_Card_Update(request):
    headers = {'User-Agent': 'request'}
    
    user = str(request.args.get('User', None))
    repo = str(request.args.get('Repo', None))
    
    pulls_url = f"{BASE_GIT_URL}/repos/{user}/{repo}/pulls"
    repo_info_url = f"{BASE_GIT_URL}/repos/{user}/{repo}"
    repo_info = requests.get(repo_info_url, headers=headers).json()
    
    response = requests.get(pulls_url, headers=headers, params={'per_page': 5, 'state': 'all'}).json()

    First_five_pulls = "First Five Pull Requests: \n"

    for pull in response:
        First_five_pulls += (f"Pull Request Title: {pull['title']}\n")
        First_five_pulls += (f"Pull Request Status: {pull['state']}\n")
        First_five_pulls += ("-----\n")
    
    Repo_URL = f"{BASE_URL}?function=Github_Repository_Card_Update&User={user}&Repo={repo}"
    
    Repository_Name = repo_info['name']
    Owner_name = f"Owner Name: {user}"

    returncard = {
                    "sections": [
{
                                    "widgets": [
        {"textParagraph": {"text": Repository_Name}},
        {"textParagraph": {"text": Owner_name}},
        {"textParagraph": {"text": First_five_pulls}}] + [
                                        {
                                            "buttonList": {
                                                "buttons": [
                    {"text": "Parent Repository", "onClick": {"action": {"function": Repo_URL}}}
                                            ]}}]}]}

    return { 
        "renderActions": {
            "action": {
                "navigations": [
                    {
                        "pushCard": returncard
                    }]}}}

def Github_ListOfIssues_Card_Update(request):
    headers = {'User-Agent': 'request'}

    user = str(request.args.get('User', None))
    repo = str(request.args.get('Repo', None))

    logging.warning('update list of issues (user/repo): ' + str(user) + '/' + str(repo))
    
    issues_url = f"{BASE_GIT_URL}/repos/{user}/{repo}/issues"
    repo_info_url = f"{BASE_GIT_URL}/repos/{user}/{repo}"
    repo_info = requests.get(repo_info_url, headers=headers).json()    
    
    
    response = requests.get(issues_url, headers=headers, params={'per_page': 5, 'state': 'all'}).json()

    First_five_issues = "First Five Issues: \n"

    for issue in response:
        First_five_issues += (f"Issue Title: {issue['title']}\n")
        First_five_issues += (f"Issue Status: {issue['state']}\n")
        First_five_issues += ("-----\n")
        
    Repo_URL = f"{BASE_URL}?function=Github_Repository_Card_Update&User={user}&Repo={repo}"
    
    Repository_Name = repo_info['name']
    Owner_name = f"Owner Name: {user}"

    returncard = {
        "sections": [
          {
            "widgets": [
                {"decoratedText":{"topLabel": f"Repository Name: {Repository_Name}"}},
        {"textParagraph": {"text": Owner_name}},
        {"textParagraph": {"text": First_five_issues}},
              {
                "buttonList": {
                  "buttons": [
                    {"text": "Parent Repository", "onClick": {"action": {"function": Repo_URL}}}
                    ]}}]}]}                 
    return { 
        "renderActions": {
            "action": {
                "navigations": [
                    {
                        "pushCard": returncard
                    }]}}}

def get_summary(user, repo, api_key):
    
    logging.warning('inside get_summary')
    # Sending GET request to Cloud Run service
    url = #CloudRun
    params = {
        'User': user,
        'Repo': repo,
        'api_key': api_key
    }
    logging.warning(f"inside get_summary with user = {user} repo = {repo} apikey = {api_key}")
    logging.warning(f"making a request to {url}")

    response = requests.get(url, params=params)

    if response.status_code == 200:
        json_response = response.json()
        return json_response
    
    else:
        logging.warning('Summarize failed to talk to Cloud Run service')    
        return None

def Summarize(request):
    user = request.args.get('User', None)
    repo = request.args.get('Repo', None)
    api_key = request.args.get('api_key')
    
    logging.warning(f"inside summarize with user = {user} repo = {repo} apikey = {api_key}")
    
    summary_json = get_summary(user, repo, api_key)
    
    if summary_json is not None:
        return { 
            "renderActions": {
                "action": {
                    "navigations": [
                        {
                            "pushCard": summary_json
                        }]}}}
    else:
        return { 
            "renderActions": {
                "action": {
                    "navigations": [
                        {
                            "pushCard": {"sections": [{"widgets": [{"textParagraph": {"text": "Failed to get data from Cloud Run service"}}]}]}
                        }]}}}