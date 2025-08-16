from route_config import route_config
from builderObjects import createDeadLetterObject
from mongoDb import db
from emailSender import send_mail
from functions import _getAllUsersToSendDeadLetterCreationEmail
import json
from pubSubPublisherAndSubscriber import publisher


class DeadLetterActions():

    @route_config(httpMethod='POST',
                  jwtRequired=False,
                  successMessage='Dead letter message created successfully')
    def createDeadLetter(self, _id: str, originalMessage: dict,
                         subscription: str, originalTopicPath: str
                         ) -> dict:

        # idempotency check
        if db.read({'_id': _id}, 'DeadLetters', findOne=True):
            return 'data already exists'

        subscriptions = publisher.list_topic_subscriptions(request={"topic": originalTopicPath})

        deadLetterObject = createDeadLetterObject(
            id=_id,
            originalMessage=originalMessage,
            subscription=subscription,
            )

        # Prepare & send an email (single API call with all recipients)
        allUsers = _getAllUsersToSendDeadLetterCreationEmail()
        recipient_emails = [
            u.email for u in allUsers if getattr(u, 'email', None)
        ]

        # Pretty JSON for original message (truncate if excessively long)
        try:
            pretty_original = json.dumps(originalMessage,
                                         ensure_ascii=False,
                                         indent=2)
        except Exception:
            pretty_original = str(originalMessage)
        if len(pretty_original) > 5000:  # safety truncation
            pretty_original = pretty_original[:5000] + "\n... (truncated)"

        subject = f"Dead Letter: {deadLetterObject.subscription}"
        html_email = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <title>New Dead Letter - {deadLetterObject.subscription} from {deadLetterObject.topic}</title>
    <meta name=\"color-scheme\" content=\"light dark\" />
    <style>
        body {{ font-family: Arial, sans-serif; background:#f5f7fa; margin:0; padding:24px; }}
        .card {{ max-width:680px; margin:0 auto; background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; }}
        .header {{ background:#0d47a1; color:#ffffff; padding:16px 24px; }}
        .header h1 {{ margin:0; font-size:20px; }}
        .meta-table {{ width:100%; border-collapse:collapse; font-size:14px; margin:16px 0 24px; }}
        .meta-table th, .meta-table td {{ text-align:left; padding:6px 8px; vertical-align:top; }}
        .meta-table th {{ width:180px; background:#f1f5f9; font-weight:600; }}
        pre {{ background:#0f172a; color:#e2e8f0; padding:16px; border-radius:6px; overflow:auto; font-size:12px; line-height:1.4; max-height:400px; }}
        .footer {{ font-size:12px; color:#64748b; margin-top:32px; }}
        @media (prefers-color-scheme: dark) {{
                body {{ background:#0f172a; }}
                .card {{ background:#1e293b; border-color:#334155; }}
                .meta-table th {{ background:#334155; color:#f1f5f9; }}
                .meta-table td {{ color:#f1f5f9; }}
                .footer {{ color:#94a3b8; }}
        }}
    </style>
 </head>
 <body>
    <div class=\"card\">
        <div class=\"header\">
            <h1>New Dead Letter Created</h1>
            <p style=\"margin:4px 0 0; font-size:13px; opacity:.85;\">Project: {deadLetterObject.subscription})</p>
        </div>
        <div style=\"padding:24px; color:#0f172a;\">
            <p style=\"margin-top:0;\">A new dead letter message has been captured and stored in the dashboard.</p>
            <table class=\"meta-table\" role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\" border=\"0\">
                <tr><th>ID</th><td>{_id}</td></tr>
                <tr><th>Subscriber Name</th><td>{deadLetterObject.subscription}</td></tr>
                <tr><th>Topic Name</th><td>{deadLetterObject.topic}</td></tr>
                <tr><th>Stored Collection</th><td>DeadLetters</td></tr>
                <tr><th>Replay Instructions</th><td>Use the dashboard action 'Retry' or the API endpoint for replay.</td></tr>
            </table>
            <h3 style=\"margin:0 0 8px; font-size:16px;\">Original Message Payload</h3>
            <pre>{pretty_original}</pre>
            <p style=\"margin-top:24px; font-size:13px;\">If this dead letter was expected you can ignore this message. Otherwise investigate the error and retry from the dashboard.</p>
            <div class=\"footer\">This is an automated notification – please do not reply directly.</div>
        </div>
    </div>
 </body>
</html>
"""
        res = db.create(deadLetterObject.model_dump(by_alias=True),
                        'DeadLetters')

        if recipient_emails:
            try:
                send_mail(recipient_emails, subject, html_email)
            except Exception as e:
                print(f"Failed to send notification email(s): {e}")

        return res


class PubSubRequests(DeadLetterActions):

    def __init__(self):
        DeadLetterActions.__init__(self)
