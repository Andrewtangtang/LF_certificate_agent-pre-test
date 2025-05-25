TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_random_question",
            "description": "Get a random practice question and its answer from the certification question database."
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_question_and_answer",
            "description": "Search for a question in the database based on input text and return the question and its answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to search for in the questions.",
                    }
                },
                "required": ["text"],
            },
        },
    },
] 