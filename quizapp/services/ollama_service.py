import ollama


def generate_ict_report(prompt):

    response = ollama.chat(

        model="llama3.2:3b",

        messages=[

            {
                "role": "user",
                "content": prompt
            }

        ]

    )


    return response["message"]["content"]