from mailjet_rest import Client


class MailJetClient:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = Client(
            auth=(self.api_key, self.api_secret), version="v3.1"
        )

    def send_templated_email(
        self,
        from_email: str,
        to_email: str,
        recipient_name: str,
        template_id: int,
        subject: str,
        variables,
    ):
        data = {
            "Messages": [
                {
                    "From": {
                        "Email": from_email,
                        "Name": "fck algos",
                    },
                    "To": [
                        {
                            "Email": to_email,
                            "Name": recipient_name,
                        }
                    ],
                    "TemplateID": template_id,
                    "TemplateLanguage": True,
                    "Subject": subject,
                    "Variables": variables,
                }
            ]
        }
        result = self.client.send.create(data=data)
        return result.json()
