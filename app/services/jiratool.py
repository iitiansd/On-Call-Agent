import os
import base64
import requests
import re
from typing import Dict, List
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from app.core.config import settings


class JiraHandler:
    def __init__(self):
        # Store API credentials
        JIRA_EMAIL = settings.JIRA_EMAIL
        JIRA_API_TOKEN = settings.JIRA_API_TOKEN
        auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Basic {encoded_auth}"
        }

        # Initialize OpenAI LLM
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)

    def get_jira_details(self, issue_id: str) -> Dict:
        """Fetch Jira issue details, parse summary, and fetch comments"""
        try:
            # Fetch issue details using the Jira REST API
            url = f"https://6sense.atlassian.net/rest/api/2/issue/{issue_id}"
            response = requests.get(url, headers=self.headers)
            import pdb; pdb.set_trace()

            if response.status_code != 200:
                return {"error": f"Failed to fetch issue details: {response.status_code}"}

            issue_data = response.json()

            # Extract summary and description from the response
            summary = issue_data.get("fields", {}).get("summary", "")
            description = issue_data.get("fields", {}).get("description", "")

            # Parse summary to extract query_summary
            query_summary = self._extract_query_summary(summary)

            # Fetch comments using the Jira REST API
            comments, ignored_comments = self._fetch_comments(issue_id)

            # Extract Observe Logs URL from the description
            observe_logs_url = self._extract_observe_logs_url(description)

            return {
                "issue_id": issue_id,
                "summary": summary,
                "query_summary": query_summary,
                "observe_logs_url": observe_logs_url,                
            }

        except Exception as e:
            return {"error": str(e)}

    def _extract_query_summary(self, summary: str) -> str:
        """Extract the query_summary by removing everything up to the last ']'"""
        # Split the summary at the last ']' and take the remaining part
        parts = summary.split("]")
        if len(parts) > 1:
            return parts[-1].strip()  # Return the part after the last ']'
        return summary  # If no ']' is found, return the original summary

    def _fetch_comments(self, issue_id: str) -> (List[Dict], List[Dict]):
        """Fetch comments for a Jira issue using the REST API"""
        url = f"https://6sense.atlassian.net/rest/api/2/issue/{issue_id}/comment"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            comments_data = response.json().get("comments", [])
            comments = []
            ignored_comments = []

            for comment in comments_data:
                author = comment.get("author", {}).get("displayName", "Unknown")
                if author == "SVC_Jira-Datadog Service Account":
                    # Add to ignored comments
                    ignored_comments.append({
                        "author": author,
                        "body": comment.get("body", ""),
                        "created": comment.get("created", "")
                    })
                else:
                    # Add to regular comments
                    comments.append({
                        "author": author,
                        "body": comment.get("body", ""),
                        "created": comment.get("created", "")
                    })

            return comments, ignored_comments
        else:
            return [], []

    def _extract_observe_logs_url(self, description: str) -> str:
        """Extract the Observe Logs URL from the description using regex"""
        # Regex to match Observe Logs URL
        observe_logs_pattern = r"https://\d+\.observeinc\.com[^\s]+"
        match = re.search(observe_logs_pattern, description)

        if match:
            return match.group(0)  # Return the first match
        return ""  # Return empty string if no match is found

    def search_issues_by_summary(self, query_summary: str) -> Dict:
        """Search Jira issues by summary using JQL and fetch comments"""
        try:
            # Construct JQL query
            jql_query = f'summary ~ "{query_summary}" ORDER BY created DESC'
            import pdb; pdb.set_trace()
            url = f"https://6sense.atlassian.net/rest/api/2/search?jql={jql_query}&maxResults=10&fields=summary,comment"

            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                return {"error": f"Failed to fetch issues: {response.status_code}"}

            issues_data = response.json().get("issues", [])
            organized_comments = []
            ignored_comments = []

            # Organize comments from the fetched issues
            for issue in issues_data:
                issue_key = issue.get("key", "")
                issue_summary = issue.get("fields", {}).get("summary", "")
                comments = issue.get("fields", {}).get("comment", {}).get("comments", [])

                # Extract the last 2-3 comments (most recent)
                recent_comments = comments[-3:] if len(comments) > 3 else comments

                excluded_authors = ["SVC_Jira-Datadog Service Account", "Another_Bot_Account"]

                for comment in recent_comments:
                    author = comment.get("author", {}).get("displayName", "Unknown")
                    
                    if author in excluded_authors:
                        # Add to ignored comments
                        ignored_comments.append({
                            "issue_key": issue_key,
                            "issue_summary": issue_summary,
                            "author": author,
                            "body": comment.get("body", ""),
                            "created": comment.get("created", "")
                        })
                    else:
                        # Add to regular comments
                        organized_comments.append({
                            "issue_key": issue_key,
                            "issue_summary": issue_summary,
                            "author": author,
                            "body": comment.get("body", ""),
                            "created": comment.get("created", "")
                        })

            # Call ChatGPT API to process or append additional information
            chatgpt_response = self._append_chatgpt_response(organized_comments)

            return {
                "query_summary": query_summary,
                "issues_found": len(issues_data),
                "chatgpt_response": chatgpt_response
            }

        except Exception as e:
            return {"error": str(e)}

    def _append_chatgpt_response(self, comments: List[Dict]) -> str:
        """Call ChatGPT API to append additional information to comments"""
        try:
            # Prepare the context for ChatGPT
            context = "\n".join([f"Issue: {comment['issue_key']}\nComment: {comment['body']}" for comment in comments])

            # Define the prompt template using LangChain's PromptTemplate
            prompt_template = PromptTemplate(
                input_variables=["context"],
                template="""
You are an expert debugger. Analyze the logs and comments from previous tickets and provide insights or resolutions based on the context.

Context:
{context}

Instructions:
1. Identify recurring issues or patterns in the logs.
2. Suggest potential resolutions or next steps.
3. If no clear resolution is found, recommend further investigation steps.

Provide your response in a clear and concise manner.
"""
            )

            # Format the prompt with the context
            prompt = prompt_template.format(context=context)

            print(f"Prompt: {prompt}")
            print("Prompt completed")

            # Call ChatGPT API synchronously
            response = self.llm.invoke(prompt)

            # Append ChatGPT response to each comment
            # for comment in comments:
            #     comment["chatgpt_response"] = response

            return response

        except Exception as e:
            # If ChatGPT API call fails, return the original comments
            print(f"Error calling ChatGPT API: {e}")
            return response


# Example usage:
# jira_handler = JiraHandler()
# issue_details = jira_handler.get_jira_details("SLA-558863")
# print(issue_details)

# Search issues by summary
# search_results = jira_handler.search_issues_by_summary("Oldest task monitor scheduler/orgupdated for team team/platform_eng")
# print(search_results)