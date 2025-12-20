from sqlalchemy.orm import Session
from app.crud.workflow import get_workflow
from app.models.workflow import Workflow
import logging
from typing import Dict, List, Any
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.crud.credentials import get_credential_by_platform
import json
import re

from app.core.constants import NODES_WITH_OUTPUT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, workflow_id: str, user_id: str, db: Session):
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.db = db
        self.workflow = None

    def load_workflow(self):
        self.workflow = get_workflow(self.db, self.workflow_id, self.user_id)
        if not self.workflow:
            raise ValueError(f"Workflow {self.workflow_id} not found for user {self.user_id}")

    def build_graph(self):
        nodes = self.workflow.nodes
        connections = self.workflow.connections
        
        if isinstance(nodes, dict):
            if "nodes" in nodes and isinstance(nodes["nodes"], list):
                nodes = nodes["nodes"]
            else:
                converted_nodes = []
                for n_id, n_data in nodes.items():
                    if isinstance(n_data, dict):
                        n_data = n_data.copy() 
                        if 'id' not in n_data:
                            n_data['id'] = n_id
                        converted_nodes.append(n_data)
                nodes = converted_nodes

        if isinstance(connections, dict):
            if "connections" in connections and isinstance(connections["connections"], list):
                connections = connections["connections"]
            else:
                 connections = list(connections.values())

        if not isinstance(nodes, list):
            nodes = []
        if not isinstance(connections, list):
            connections = []

        node_map = {node['id']: node for node in nodes}
        adj_list: Dict[str, List[str]] = {node['id']: [] for node in nodes}
        
        in_degree: Dict[str, int] = {node['id']: 0 for node in nodes}

        for conn in connections:
            source = conn.get('source')
            target = conn.get('target')
            
            if source and target and source in node_map and target in node_map:
                adj_list[source].append(target)
                in_degree[target] += 1
        
        return adj_list, in_degree, node_map

    def get_execution_order(self):
        adj_list, in_degree, node_map = self.build_graph()
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        execution_order = []

        while queue:
            node_id = queue.pop(0)
            execution_order.append(node_map[node_id])

            for neighbor in adj_list[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(execution_order) != len(node_map):
            logger.warning("Cycle detected in workflow graph or disconnected components not reachable.")
            
        return execution_order
    def _resolve_variables(self, value: Any, context: Dict[str, Any]) -> Any:
        """
        Recursively resolves string variables in the format {{nodeId.path.to.value}}
        using the provided context dictionary.
        """
        if isinstance(value, str):
            # Regex to find {{...}} patterns
            pattern = r"\{\{(.*?)\}\}"
            matches = re.findall(pattern, value)
            
            if not matches:
                return value
            
            for match in matches:
                key = match.strip()
                resolved_val = self._get_value_from_context(key, context)
                
                # If the entire string is just the variable, return the type-preserved value
                if value == f"{{{{{match}}}}}":
                    if isinstance(resolved_val, dict):
                         if 'text' in resolved_val:
                             return resolved_val['text']
                         elif 'output' in resolved_val:
                             return resolved_val['output']
                    return resolved_val
                
                # Smart Stringification for interpolation
                replacement_str = str(resolved_val)
                if isinstance(resolved_val, dict):
                    # Try to extract meaningful text content if available
                    if 'text' in resolved_val:
                        replacement_str = str(resolved_val['text'])
                    elif 'output' in resolved_val:
                        replacement_str = str(resolved_val['output'])
                    # If specific paths were requested (handled by get_value), we won't be here with a full dict usually,
                    # Unless the user asked for {{node.output}} and output is a dict.
                
                value = value.replace(f"{{{{{match}}}}}", replacement_str)
            return value
        
        elif isinstance(value, dict):
            return {k: self._resolve_variables(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_variables(v, context) for v in value]
        else:
            return value

    def _get_value_from_context(self, path: str, context: Dict[str, Any]) -> Any:
        """
        Traverses the dot-separated path in the context dictionary.
        """
        parts = path.split('.')
        current = context
        
        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    logger.warning(f"Path traversal failed at part '{part}' for path '{path}'")
                    return None 
            return current
        except Exception as e:
            logger.error(f"Error resolving path '{path}': {e}")
            return None

    def execute_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        node_id = node.get('id')
        data = node.get('data', {})

        resolved_data = self._resolve_variables(data, context)
        node_type = resolved_data.get('type')
        if not node_type:
             node_type = node.get('type', 'unknown')

        logger.info(f"Executing node: {node_id} (Type: {node_type})")
        
        try:
            if node_type == 'telegram-api':
                return self._execute_telegram(node_id, resolved_data)
            elif node_type == 'gemini':
                return self._execute_gemini(node_id, resolved_data)
            elif node_type == 'email-send' or node_type == 'gmail':
                 return self._execute_email(node_id, resolved_data)
            elif node_type == 'MANUAL':
                 return {"node_id": node_id, "status": "success", "output": "Manual trigger executed"}
            else:
                 return {"node_id": node_id, "status": "success", "output": f"Pass {node_type}"}
        except Exception as e:
            logger.error(f"Execution failed for node {node_id}: {e}")
            raise e

    def _execute_telegram(self, node_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing Telegram node {node_id}")
        config = data.get('config', {})
        chat_id = config.get('chatId')
        message = config.get('message')

        if not chat_id or not message:
             raise ValueError("Telegram node missing 'chatId' or 'message' in config")

        cred = get_credential_by_platform(self.db, self.user_id, "telegram")
        if not cred:
            raise ValueError("No Telegram credentials found for user")
        
        if isinstance(cred.data, dict):
            token = cred.data.get('botToken')
        
        if not token:
             raise ValueError("Telegram credential invalid: missing 'botToken'")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        
        return {
            "node_id": node_id,
            "status": "success",
            "output": resp.json()
        }

    def _execute_gemini(self, node_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing Gemini node {node_id}")
        config = data.get('config', {})
        prompt = config.get('prompt')
        model = config.get('model', 'gemini-2.5-flash')

        if not prompt:
            raise ValueError("Gemini node missing 'prompt' in config")

        cred = get_credential_by_platform(self.db, self.user_id, "gemini")
        if not cred:
            raise ValueError("No Gemini credentials found for user")

        if isinstance(cred.data, dict):
            api_key = cred.data.get('apiKey')
        else:
            try:
                data_json = json.loads(cred.data)
                api_key = data_json.get('apiKey')
            except (json.JSONDecodeError, TypeError):
                raise ValueError("Gemini credential invalid: data format error")

        if not api_key:
            raise ValueError("Gemini credential invalid: missing 'apiKey'")
        
        model_mapping = {
            'gemini-2.5-flash': 'gemini-2.5-flash',
            'gemini-2.5-pro': 'gemini-2.5-flash', # temperory -> because pro model gives 429 too many requests
        }
        
        model = model_mapping.get(model, model)

        print(model)
        
        # Fallback to a valid default if empty
        if not model:
            model = 'gemini-2.5-flash'
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            
            response_json = resp.json()
            generated_text = response_json['candidates'][0]['content']['parts'][0]['text']
            return {
                "node_id": node_id,
                "status": "success",
                "output": {
                    "text": generated_text,
                    "raw": response_json
                }
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return {
                "node_id": node_id,
                "status": "success",
                "output": resp.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {e}")
            raise


    def _execute_email(self, node_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing Email node {node_id}")
        config = data.get('config', {})
        recipient = config.get('to')
        subject = config.get('subject')
        body = config.get('body')

        if not recipient or not subject or not body:
             raise ValueError("Email node missing 'to', 'subject', or 'body'")

        cred = get_credential_by_platform(self.db, self.user_id, "gmail")
        if not cred:
             raise ValueError("No Gmail credentials found for user")
             
        if isinstance(cred.data, dict):
             sender_email = cred.data.get('email')
             app_password = cred.data.get('password')
        else:
             try:
                 cred_data = json.loads(cred.data)
                 sender_email = cred_data.get('email')
                 app_password = cred_data.get('password')
             except (json.JSONDecodeError, TypeError):
                 raise ValueError("Gmail credential invalid: data format error")
        
        if not sender_email or not app_password:
             raise ValueError("Gmail credential invalid: missing 'email' or 'password'")

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Standard Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)

        return {
            "node_id": node_id,
            "status": "success",
            "output": f"Email sent to {recipient}"
        }

    def execute(self) -> Dict[str, Any]:
        self.load_workflow()
        
        try:
            execution_order = self.get_execution_order()
        except ValueError as e:
            return {"status": "failed", "error": str(e)}

        print("Execution order:", execution_order)
        
        results = {}
        context = {}

        logger.info(f"Starting execution of workflow {self.workflow_id}")

        for node in execution_order:
            try:
                # Resolve variables before execution using the current context
                result = self.execute_node(node, context)
                results[node['id']] = result
                
                # Update context for subsequent nodes ONLY if this node type produces output
                node_data = node.get('data', {})
                node_type = node_data.get('type')
                if not node_type:
                     node_type = node.get('type', 'unknown')

                if node_type in NODES_WITH_OUTPUT:
                    context[node['id']] = result
                
                if result.get("status") == "failed":
                    logger.error(f"Node {node['id']} failed. Stopping execution.")
                    return {"status": "failed", "results": results}

            except Exception as e:
                logger.error(f"Error executing node {node['id']}: {e}")
                results[node['id']] = {"status": "error", "error": str(e)}
                return {"status": "failed", "error": str(e), "results": results}
        
        logger.info(f"Workflow {self.workflow_id} completed successfully")
        return {"status": "completed", "results": results}
