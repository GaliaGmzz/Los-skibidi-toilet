from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

endpoint = "https://uaem.cognitiveservices.azure.com/"
key = "AErOecE6knkRaaA8JRhfxHZLWjxH81lVzkMZz9PzxubJVDMx60GwJQQJ99CEAC1i4TkXJ3w3AAALACOG0GJx"

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

ROW_TOL = 0.010
FUZZY_CUTOFF = 0.82
DEBUG = False
