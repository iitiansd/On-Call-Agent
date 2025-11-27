import os
import base64
import requests
from typing import Dict, Tuple, Any
from langchain.llms import OpenAI
from langchain.chains.query_constructor.base import AttributeInfo, StructuredQueryOutputParser, get_query_constructor_prompt
# from langchain.retrievers.self_query.weaviate import WeaviateTranslator
# from langchain.chat_models import ChatOpenAI
from app.core.config import settings
from datetime import datetime, timezone
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackHandler:
    def __init__(self):
        # Store API key
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

#     def _get_todays_date(self):
#         return datetime.now(timezone.utc).date().isoformat()
    
#     def _get_todays_day(self):
#         # Get the current day of the week
#         current_utc_datetime = datetime.utcnow()
#         todays_day = current_utc_datetime.strftime("%A")
#         return todays_day

#     def _translate_query(self, query: str, structured_query: Any, search_kwargs: Dict[str, Any]) -> Dict[str, Any]:
#         # Initialize query translator
#         structured_query_translator = WeaviateTranslator()
        
#         # Translate structured query
#         new_query, new_kwargs = structured_query_translator.visit_structured_query(structured_query)
        
#         # Extract where_filter from translated query
#         where_filter = new_kwargs.get("where_filter", {})
        
#         # Prepare arguments array
#         arguments = []
#         operator_map = {
#             "Equal": "eq",
#             "GreaterThan": "gt",
#             "LessThan": "lt",
#             "GreaterThanEqual": "gte",
#             "LessThanEqual": "lte"
#         }

#         for operand in where_filter.get("operands", []):
#             attribute = operand["path"][0]
#             comparator = operator_map.get(operand["operator"], "eq")
#             value = operand.get("valueText", "")

#             # Handle date formatting
#             if attribute == "date":
#                 try:
#                     # Parse date with multiple format support
#                     dt = None
#                     for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
#                         try:
#                             dt = datetime.strptime(value, fmt)
#                             break
#                         except ValueError:
#                             continue
                    
#                     if not dt:
#                         raise ValueError(f"Unrecognized date format: {value}")
                    
#                     formatted_date = dt.strftime("%Y-%m-%d")
#                     value = {"date": formatted_date, "type": "date"}
#                     arguments.append({
#                         "comparator": comparator,
#                         "attribute": attribute,
#                         "value": value
#                     })
#                 except Exception as e:
#                     print(f"Date parsing error: {str(e)}")
#                     continue
#             else:
#                 # Handle channel name cleanup
#                 if attribute in ["in", "in_private"]:
#                     value = value.replace(" channel", "").strip()
                
#                 arguments.append({
#                     "comparator": comparator,
#                     "attribute": attribute,
#                     "value": value
#                 })
        
#         # Extract core content query
#         content_query = structured_query.query.strip() if structured_query.query else query
        
#         return {
#             "query": content_query,
#             "filter": {
#                 "operator": "and" if len(arguments) > 1 else "or",
#                 "arguments": arguments
#             }
#         }

#     def _self_querying_over_slack_search(self, query):
#         # Get today's date and day
#         todays_date = self._get_todays_date()
#         # todays_day = self._get_todays_day()

#         # Define metadata fields for Slack search
#         metadata_field_info = [
#             AttributeInfo(
#                 name="in",
#                 description="Public Slack channel where content was shared. Always remove 'channel' suffix if present. Example: 'plantinum-platform' instead of 'plantinum-platform channel'",
#                 type="string",
#             ),
#             AttributeInfo(
#                 name="in_private",
#                 description="Private Slack channel where content was shared. Always remove 'channel' suffix if present.",
#                 type="string",
#             ),
#             AttributeInfo(
#                 name="from",
#                 description="The person who shared the content. Example: 'Febin'",
#                 type="string",
#             ),
#             AttributeInfo(
#                 name="date",
#                 description="Date filter using 'after <date>' (gt) or 'before <date>' (lt). Supports formats: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY. Example: 'after 2024-08-03'",
#                 type="date",
#             )
#         ]

#         document_content_description = "The actual message content or topic being searched for. Example: 'Cronjob failure monitor for cronjob/alerts-v2-send-notifications'"
#        # Initialize LLM model
#         llm = ChatOpenAI(temperature=0)

#         # Create structured query prompt
#         prompt = get_query_constructor_prompt(
#             document_content_description, metadata_field_info
#         )

#         # Initialize query parser
#         output_parser = StructuredQueryOutputParser.from_components()
#         query_constructor = prompt | llm | output_parser

#         # Generate structured query
#         structured_query = query_constructor.invoke({"query": query})

#         # Translate query for Slack search
#         structured_translated_query = self._translate_query(query, structured_query, {})


#         formatted_query = self._translate_query(query, structured_query, {})
#         return formatted_query
#         # return structured_translated_query
        
#         # structured_query = self.convert_to_slack_query(structured_translated_query)

#     def search_slack_messages(token, keyword=None, from_user=None, in_channel=None, after_date=None, before_date=None):
#         """
#         Searches Slack messages based on the provided parameters.

#         Parameters:
#         - token (str): Slack API token with necessary scopes.
#         - keyword (str): The main keyword or phrase to search for.
#         - from_user (str): The username to filter messages from (e.g., 'john').
#         - in_channel (str): The channel name to search within (e.g., 'project').
#         - after_date (str): The start date to filter messages (format: 'YYYY-MM-DD').
#         - before_date (str): The end date to filter messages (format: 'YYYY-MM-DD').

#         Returns:
#         - list: A list of matching messages.
#         """
#         import pdb; pdb.set_trace()
#         # Initialize the Slack client
#         token = settings.SLACK_TOKEN
#         client = WebClient(token=token)

#         # Build the query string
#         query_parts = []

#         if keyword:
#             query_parts.append(keyword)

#         if from_user:
#             query_parts.append(f"from:@{from_user}")

#         if in_channel:
#             query_parts.append(f"in:{in_channel}")

#         if after_date:
#             query_parts.append(f"after:{after_date}")

#         if before_date:
#             query_parts.append(f"before:{before_date}")

#         query = ' '.join(query_parts)

#         try:
#             # Call the search.messages method
#             print(f"query{query}")
#             response = client.search_messages(query=query,  count=3)

#             # Check if the response is successful
#             if response['ok']:
#                 # Return the list of matching messages
#                 return response['messages']['matches']
#             else:
#                 print("Error in response:", response['error'])
#                 return []

#         except SlackApiError as e:
#             print(f"{e}")
#             print(f"Slack API Error: {e.response['error']}")
#             return []
