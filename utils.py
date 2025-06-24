import json
from io import StringIO
from waii_sdk_py.query import GetQueryResultResponse
from waii_sdk_py.chat import ChatResponse


def serialize_query_result_response(response: GetQueryResultResponse, limit=10):
    """Serialize a query result response to a formatted string.

    Args:
        response: The query result response to serialize
        limit: Maximum number of rows to include in the output

    Returns:
        A formatted string containing the query results
    """
    try:
        df = response.to_pandas_df()
        output = StringIO()
        df.head(limit).to_csv(output, index=False)
        csv_string = output.getvalue().strip()

        # Truncate long lines
        lines = csv_string.split('\n')
        truncated_lines = []
        for line in lines:
            if len(line) > 500:
                truncated_lines.append(line[:497] + '...')
            else:
                truncated_lines.append(line)
        csv_string = '\n'.join(truncated_lines)

        if len(df) > limit:
            csv_string += "\n..."

        # if the csv string is too long (5k), truncate it
        if len(csv_string) > 5000:
            csv_string = csv_string[:5000] + "..."

        csv_string += f"\n--\n{len(df)} row(s)"
        return csv_string
    except Exception as e:
        error_msg = f"Error serializing query result: {str(e)}"
        return f"Error processing results: {error_msg}"



def apply_concierge_formatting(chat_response: ChatResponse):

    def concierge_widget(data: dict | list, data_type: str) -> str:
        serialized_data = json.dumps(
            dict(data_type=data_type, data=data),
            indent=2,
        )
        return f"\n%BEGIN_JSON%\n{serialized_data}\n%END_JSON%\n"

    def remove(substr: str): chat_response.response.replace(substr, "")
    def append(section: str): chat_response.response += "\n" + section.strip()

    try:
        references_section = ""
        if "<query>" in chat_response.response:
            references_section+=f"Generated query:\n```\n{chat_response.response_data.query.query}\n```\n"
        if "<data>" in chat_response.response:
            append(concierge_widget(chat_response.response_data.data.rows, data_type="table"))
        if "<chart>" in chat_response.response:
            chart_spec = json.loads(chat_response.response_data.chart.chart_spec.chart)
            chart_spec["data"] = dict(values=chat_response.response_data.data.rows)
            references_section += concierge_widget(chart_spec, data_type="chart")
        return chat_response.response + "\n" + references_section
    except Exception as e:
        error_msg = f"Error processing chat response: {str(e)}"
        return f"Error processing response: {error_msg}"
