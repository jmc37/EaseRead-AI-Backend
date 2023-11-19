from transformers import pipeline
from PIL import Image

pipe = pipeline("document-question-answering", model="impira/layoutlm-document-qa")

question = "What is the purchase amount?"
image = Image.open("images/invoice-template-us-neat-750px.png")

pipe(image=image, question=question)
print(pipe(image=image, question=question))
## [{'answer': '20,000$'}]
