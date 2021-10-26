from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential


endpoint = "https://invoicesform.cognitiveservices.azure.com/"

key = "aadae7e08dfe44b8b29fef3495905f7f"

form_recognizer_client = FormRecognizerClient(endpoint, AzureKeyCredential(key))


def ai_formrecognizer(path):
    
    with open(path, "rb") as fd:
            form = fd.read()

    #recognizer result :

    poller_2 =  form_recognizer_client.begin_recognize_content(form=form)
    pages = poller_2.result()
    return pages