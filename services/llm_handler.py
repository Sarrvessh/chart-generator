import json
import httpx
from typing import Dict, Any

class LLMHandler:
    """Handles LLM interactions for chart specification generation (Ollama compatible)"""

    def __init__(self, endpoint: str, api_key: str, model: str):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key  # Not required for Ollama, but kept for compatibility
        self.model = model

    def create_system_prompt(self, data_metadata: Dict[str, Any]) -> str:
        """Create system prompt with data context"""
        return f"""You are a data visualization expert. Given a user's natural language request and data metadata,
        generate a JSON specification for creating a chart.

        Available data columns: {json.dumps(data_metadata['columns'])}
        Numerical columns: {json.dumps(data_metadata['numerical_columns'])}
        Categorical columns: {json.dumps(data_metadata['categorical_columns'])}
        Datetime columns: {json.dumps(data_metadata['datetime_columns'])}
        Row count: {data_metadata['row_count']}

        CRITICAL INSTRUCTIONS (follow exactly):
        - Output MUST be exactly one valid JSON object (or JSON array if explicitly required) and nothing else.
        - Do NOT include any explanatory text, markdown, code fences (```), or surrounding punctuation.
        - If you cannot form a valid spec, return an empty JSON object: {{}}.

        Chart Type Requirements:
        - "bar": Use categorical x_axis, optional numeric y_axis. If no y_axis, counts categorical values.
        - "line": Requires numeric x_axis (time/index) and numeric y_axis. Good for trends.
        - "scatter": Requires numeric x_axis and numeric y_axis. For relationships.
        - "pie": Use categorical x_axis. Shows proportions of categories.
        - "histogram": MUST use numeric x_axis only. Shows distribution of numeric values.
        - "heatmap": Automatically correlates numeric columns. No x_axis/y_axis needed.
        - "area": Requires numeric x_axis and numeric y_axis. Stacked area visualization.
        - "box": Use categorical x_axis (optional) and numeric y_axis. Shows data distribution.

        The JSON object must follow this structure:
        {{
            "chart_type": "bar|line|scatter|pie|heatmap|area|histogram|box",
            "x_axis": "column_name",
            "y_axis": "column_name or null",
            "color_by": "column_name or null",
            "aggregation": "sum|mean|count|min|max|none",
            "filters": [],
            "title": "descriptive chart title",
            "x_label": "x axis label",
            "y_label": "y axis label",
            "customization": {{
                "color_scheme": "default|viridis|plasma|coolwarm",
                "show_legend": true,
                "data_labels": false
            }}
        }}

        Rules:
        1. Only use columns that exist in the data.
        2. For "histogram", ALWAYS choose from numerical columns: {json.dumps(data_metadata['numerical_columns'])}.
        3. For "line", "scatter", "area": choose numeric x_axis and numeric y_axis.
        4. For "pie", "bar": choose categorical or string x_axis.
        5. Match chart type to the data and user request.
        6. Return ONLY the JSON object and nothing else under any circumstances.
        7. Ensure all column names are valid and match exactly (case-sensitive).
        """

    async def parse_user_request(self, user_query: str, data_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user query using Ollama and generate chart spec"""
        system_prompt = self.create_system_prompt(data_metadata)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        url = f"{self.endpoint}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False 
        }

        def extract_json_from_text(text: str):
            """Find and return the first valid JSON object or array in `text`.

            This scans for the first '{' or '[' and then balances braces/brackets
            to locate the matching end. It returns the parsed Python object.
            """
            if not text:
                raise ValueError("Empty text from LLM response")

            # Find earliest opening brace or bracket
            idx_brace = text.find('{')
            idx_bracket = text.find('[')
            candidates = [i for i in (idx_brace, idx_bracket) if i != -1]
            if not candidates:
                raise ValueError("No JSON object or array found in LLM response")

            start_idx = min(candidates)
            open_char = text[start_idx]
            close_char = '}' if open_char == '{' else ']'

            stack = []
            end_idx = -1
            for i in range(start_idx, len(text)):
                ch = text[i]
                if ch == '{' or ch == '[':
                    stack.append(ch)
                elif ch == '}' or ch == ']':
                    if not stack:
                        # unexpected closing
                        raise ValueError('Malformed JSON: unexpected closing bracket')
                    stack_pop = stack.pop()
                    # optional sanity: ensure matching pairs
                    if (stack_pop == '{' and ch != '}') or (stack_pop == '[' and ch != ']'):
                        raise ValueError('Malformed JSON: mismatched brackets')
                    if not stack:
                        end_idx = i + 1
                        break

            if end_idx == -1:
                raise ValueError("Malformed JSON: unbalanced brackets in LLM response")

            json_str = text[start_idx:end_idx]
            return json.loads(json_str)

        try:
            async with httpx.AsyncClient(timeout=40) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                # Try to parse the API envelope first; if that fails, fall back to raw text.
                content = None
                try:
                    response_data = response.json()
                except ValueError:
                    # Not JSON (or streaming leftovers), use raw text
                    raw = response.text
                    content = raw.strip()
                else:
                    # Common possible places for model output (support multiple LLM envelopes)
                    if isinstance(response_data, dict):
                        # Ollama-style: {'message': {'content': '...'}}
                        msg = response_data.get('message') or response_data.get('choices')
                        if isinstance(msg, dict) and 'content' in msg:
                            content = msg['content'].strip()
                        elif isinstance(msg, list):
                            # choices list or messages list
                            parts = []
                            for c in msg:
                                if isinstance(c, dict):
                                    # try message.content or text
                                    if 'message' in c and isinstance(c['message'], dict) and 'content' in c['message']:
                                        parts.append(c['message']['content'])
                                    elif 'content' in c:
                                        parts.append(c['content'])
                                    elif 'text' in c:
                                        parts.append(c['text'])
                            content = '\n'.join([p for p in parts if p]).strip()
                        else:
                            # try other common keys
                            content = response_data.get('content') or response_data.get('text') or ''
                            content = (content or '').strip()

                if not content:
                    raise ValueError('Could not extract model output from response')

                try:
                    # Use the robust JSON extraction
                    chart_spec_dict = extract_json_from_text(content)
                    chart_spec = self.validate_and_enhance_spec(chart_spec_dict, data_metadata)
                    return chart_spec

                except json.JSONDecodeError as e:
                    raise ValueError(f"LLM returned invalid JSON: {str(e)}\nRaw content: {content}")

        except Exception as e:
            raise Exception(f"Error calling Ollama LLM: {str(e)}")

    def validate_and_enhance_spec(self, spec: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate chart specification against available data"""
        try:
            all_columns = metadata['columns']

            # Normalize filters provided by the LLM into the expected shape
            raw_filters = spec.get('filters')
            if isinstance(raw_filters, list):
                normalized_filters = []
                op_map = {
                    '=': '==', '==': '==', 'equals': '==', 'is': '==',
                    '!=': '!=', 'neq': '!=', 'not equals': '!=',
                    '>': '>', '<': '<', '>=': '>=', '<=': '<='
                }

                for f in raw_filters:
                    if not isinstance(f, dict):
                        continue
                    col = f.get('column') or f.get('column_name') or f.get('col') or f.get('field')
                    op = f.get('operator') or f.get('op') or f.get('relation') or f.get('operator_symbol')
                    if 'value' in f:
                        val = f.get('value')
                    elif 'val' in f:
                        val = f.get('val')
                    elif 'v' in f:
                        val = f.get('v')
                    else:
                        val = None

                    if isinstance(op, str):
                        op_clean = op.strip().lower()
                        op_norm = op_map.get(op_clean, op_clean)
                    else:
                        op_norm = op

                    if col and op_norm and val is not None:
                        # Prefer exact column name match, otherwise try case-insensitive
                        if col in all_columns:
                            normalized_filters.append({'column': col, 'operator': op_norm, 'value': val})
                        else:
                            matches = [c for c in all_columns if c.lower() == str(col).lower()]
                            if matches:
                                normalized_filters.append({'column': matches[0], 'operator': op_norm, 'value': val})
                            else:
                                # skip filters that reference non-existent columns
                                continue

                spec['filters'] = normalized_filters

            # Validate x/y/color columns against available columns
            if spec.get('x_axis') and spec['x_axis'] not in all_columns:
                raise ValueError(f"Column '{spec['x_axis']}' not found in data. Available: {all_columns}")
            if spec.get('y_axis') and spec['y_axis'] not in all_columns:
                spec['y_axis'] = None
            if spec.get('color_by') and spec['color_by'] not in all_columns:
                spec['color_by'] = None

            if not spec.get('aggregation'):
                if spec.get('y_axis') in metadata.get('numerical_columns', []):
                    spec['aggregation'] = 'mean'
                else:
                    spec['aggregation'] = 'count'

            if not spec.get('title'):
                spec['title'] = f"{spec.get('chart_type', 'Chart').capitalize()} Chart"
            if not spec.get('x_label'):
                spec['x_label'] = spec.get('x_axis')
            if not spec.get('y_label'):
                spec['y_label'] = spec.get('y_axis', 'Value')

            return spec
        except Exception as e:
            raise ValueError(f"Chart specification validation failed: {str(e)}")

def create_llm_handler(endpoint: str, api_key: str, model: str):
    return LLMHandler(endpoint, api_key, model)
