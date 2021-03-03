import tkinter as T
from tkinter import filedialog
from tkinter.ttk import Progressbar
import json
import re
import os
import csv
from PyPDF2 import PdfFileReader
from google.cloud import vision
from google.cloud import storage
from google.cloud import automl

top = T.Tk(className='Capstone project')
w = 500
h = 500
ws = top.winfo_screenwidth()
hs = top.winfo_screenheight()
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)
top.geometry('%dx%d+%d+%d' % (w, h, x, y))
top.config(bg = '#EDEDED')

ltitle = T.Label(text = "CAPSTONE PROJECT")
ltitle.place(relx = 0.5, rely = 0.5, anchor = 'n')
ltitle.pack(pady=20)
ltitle.config(font=("Times", 18), bg = "#EDEDED")

lhead = T.Label(text = "Upload Patent PDF files for Analysis")
lhead.place(relx = 0.5, rely = 0.5, anchor = 'n')
lhead.pack(pady=30)
lhead.config(font=("Times", 18), bg = "#EDEDED")

def helloCallBack():
    global filerem,p,l2,l3,lfile
    filenames = filedialog.askopenfilenames(parent=top,title='Select a file or multiple files',filetypes=[("PDF files", "*.pdf")])
    lst = list(filenames)
    lst_len = len(lst)

    if filenames == '':
        return None
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'/Users/anmolnahariya/Desktop/GVA/Account_key.json'


    for i in range(lst_len):
        filerem = T.Label(text=f"Files Remaining : {lst_len - i}")
        filerem.place(relx=0.5, rely=0.5, anchor='n')
        filerem.pack(pady=5)
        filerem.config(font=("Times", 18))

        p = Progressbar(top, orient='horizontal', length=200, mode="determinate", takefocus=True, maximum=100)
        p.pack()

        l2 = T.Label(text="Please Wait...")
        l2.place(relx=0.5, rely=0.5, anchor='s')
        l2.pack(pady=5)
        l2.config(font=("Times", 18))
        top.update()

        p['value'] = 20
        top.update()

        # Selected File
        bucket_name = "my_pdf_bucket_test"
        source_file_name = f"{lst[i]}"
        head, tail = os.path.split(source_file_name)
        destination_blob_name = tail

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)

        # VISION API
        client = vision.ImageAnnotatorClient()

        mime_type = 'application/pdf'

        feature = vision.Feature(
            type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

        gcs_source_uri = f'gs://my_pdf_bucket_test/{destination_blob_name}'
        gcs_source = vision.GcsSource(uri=gcs_source_uri)
        input_config = vision.InputConfig(
            gcs_source=gcs_source, mime_type=mime_type)

        storage_client = storage.Client()
        match = re.match(r'gs://([^/]+)/(.+)', gcs_source_uri)
        bucket_name = match.group(1)
        file_name = match.group(2)

        bucket = storage_client.get_bucket(bucket_name)
        blob_list_2 = list(bucket.list_blobs(prefix=file_name))
        for blob in blob_list_2:
            blob.download_to_filename(f'/Users/anmolnahariya/Desktop/GVA/{file_name}')

        with open(f'/Users/anmolnahariya/Desktop/GVA/{file_name}', "rb") as pdf_file:
            pdf_reader = PdfFileReader(pdf_file)
            pg_num = pdf_reader.numPages

        batch_size = pg_num

        gcs_destination_uri = f'gs://my_pdf_to_json/{destination_blob_name}'
        gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
        output_config = vision.OutputConfig(
            gcs_destination=gcs_destination, batch_size=batch_size)

        async_request = vision.AsyncAnnotateFileRequest(
            features=[feature], input_config=input_config,
            output_config=output_config)

        p['value'] = 40
        top.update()

        operation = client.async_batch_annotate_files(
            requests=[async_request])
        p['value'] = 50
        operation.result(timeout=420)

        bucket = storage_client.get_bucket('my_pdf_to_json')
        p['value'] = 60
        blob_list = list(bucket.list_blobs(prefix=destination_blob_name))

        print('\n')
        p['value'] = 70
        output = blob_list[0]
        json_string = output.download_as_string()
        response = json.loads(json_string)

        p['value'] = 75
        top.update()

        for i in range(pg_num):
            page_response = response['responses'][i]
            annotation = page_response['fullTextAnnotation']
            text = str(annotation['text'])

        # AUTOML API
        p['value'] = 80
        project_id = "root-stock-291103"
        model_id = "TEN2727406762419290112"

        csvfile = open(f"/Users/anmolnahariya/Desktop/Pfizer_Project/CSV/Patent_data.csv", "a")
        csvwriter = csv.writer(csvfile)
        row_1 = []
        row_2 = []
        p['value'] = 85
        prediction_client = automl.PredictionServiceClient()

        model_full_id = automl.AutoMlClient.model_path(
            project_id, "us-central1", model_id
        )

        text_snippet = automl.TextSnippet(
            content=text, mime_type="text/plain"
        )
        payload = automl.ExamplePayload(text_snippet=text_snippet)
        p['value'] = 95
        top.update()
        response = prediction_client.predict(name=model_full_id, payload=payload)
        for annotation_payload in response.payload:
            row_1.append(format(annotation_payload.display_name))
            text_segment = annotation_payload.text_extraction.text_segment
            row_2.append(format(text_segment.content))
        csvwriter.writerow(["File", gcs_source_uri])
        csvwriter.writerow(row_1)
        csvwriter.writerow(row_2)

        p['value'] = 100
        p.destroy()
        top.update()
        filerem.destroy()
        top.update()
        l2.destroy()
    top.update()
    l3 = T.Label(text=f"Done! \n Selected Files have been analyzed. \n \n")
    l3.place(relx=0.5, rely=0.5, anchor='s')
    l3.pack()
    l3.config(font=("Times", 18), bg = '#EDEDED')
    top.update()

def openfile():
    os.system("open -n /Users/anmolnahariya/Desktop/Pfizer_Project/CSV/Patent_data.csv")
    filerem.destroy()
    p.destroy()
    l2.destroy()
    l3.destroy()


select_button = T.Button(top, text ="Select files to upload", command = helloCallBack, width='25', height='2')
select_button.config(font=("Times", 18))
select_button.pack()

view_button = T.Button(top, text ="View document table", command = openfile, width='25', height='2')
view_button.config(font=("Times", 18))
view_button.pack(pady=30)
top.mainloop()
