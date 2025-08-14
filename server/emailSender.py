import requests

def send_mail(to, subject, htmlContent):
    try:
        if not isinstance(to, list):
            raise Exception(
                'The to parameter must be a list of receiver email addresses.')

        to_str = ', '.join(to) if isinstance(to, list) else to

        payload = {
            'to': to_str,
            'subject': subject,
            'htmlContent': htmlContent
        }
        response = requests.post('https://sendemail-euu6rexb4q-as.a.run.app',
                                 json=payload)

        if response.status_code == 200:
            print('Request to email sender API was successful.')
        else:
            print(
                f'Failed to send request to email sender API. Status code: {response.status_code}'
            )
            print(f'Response: {response.text}')

    except Exception as e:
        print(f"Error: {e}")


# Example usage
if __name__ == '__main__':
    send_mail(['ladiaadrian@gmail.com'], 'Test Subject multiple',
              '<h1>This is a test email</h1>')
