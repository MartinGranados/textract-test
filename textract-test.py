import boto3
import io
from trp import Document
from io import BytesIO
import sys

import math
from PIL import Image, ImageDraw, ImageFont

def ShowBoundingBox(draw, box, width, height, boxColor):

    left = width * box['Left']
    top = height * box['Top']
    draw.rectangle([left, top, left + (width * box['Width']), top + (height * box['Height'])], outline = boxColor)

def ShowSelectedElement(draw, box, width, height, boxColor):

    left = width * box['Left']
    top = height * box['Top'] 
    draw.rectangle([left,top, left + (width * box['Width']), top +(height * box['Height'])],fill=boxColor)  

# Displays information about a block returned by text detection and text analysis
def DisplayBlockInformation(block):
    print('Id: {}'.format(block['Id']))
    if 'Text' in block:
        print('    Detected: ' + block['Text'])
    print('    Type: ' + block['BlockType'])
   
    if 'Confidence' in block:
        print('    Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

    if block['BlockType'] == "LINE":
        print('\033[94m' + block["Text"] + '\033[0,')

    

    # if block['BlockType'] == 'CELL':
    #     print("    Cell information")
    #     print("        Column:" + str(block['ColumnIndex']))
    #     print("        Row:" + str(block['RowIndex']))
    #     print("        Column Span:" + str(block['ColumnSpan']))
    #     print("        RowSpan:" + str(block['ColumnSpan']))    
    
    # if 'Relationships' in block:
    #     print('    Relationships: {}'.format(block['Relationships']))
    # print('    Geometry: ')
    # print('        Bounding Box: {}'.format(block['Geometry']['BoundingBox']))
    # print('        Polygon: {}'.format(block['Geometry']['Polygon']))
    
    # if block['BlockType'] == "KEY_VALUE_SET":
    #     print ('    Entity Type: ' + block['EntityTypes'][0])
    
    # if block['BlockType'] == 'SELECTION_ELEMENT':
    #     print('    Selection element detected: ', end='')

    #     if block['SelectionStatus'] =='SELECTED':
    #         print('Selected')
    #     else:
    #         print('Not selected')    
    
    # if 'Page' in block:
    #     print('Page: ' + block['Page'])
    # print()

def process_text_analysis(bucket, document):

    #Get the document from S3
    s3_connection = boto3.resource('s3')
                          
    s3_object = s3_connection.Object(bucket,document)
    s3_response = s3_object.get()

    stream = io.BytesIO(s3_response['Body'].read())
    image=Image.open(stream)

    # Analyze the document
    client = boto3.client('textract')
    
    image_binary = stream.getvalue()
    response = client.analyze_document(Document={'Bytes': image_binary},
        FeatureTypes=["TABLES", "FORMS"])
    # response = client.start_document_analysis(Document={'Bytes': image_binary},
    #     FeatureTypes=["TABLES", "FORMS"])
  

    # Alternatively, process using S3 object
    #response = client.analyze_document(
    #    Document={'S3Object': {'Bucket': bucket, 'Name': document}},
    #    FeatureTypes=["TABLES", "FORMS"])
    doc = Document(response)
    
    #Get the text blocks
    blocks=response['Blocks']
    width, height =image.size  
    draw = ImageDraw.Draw(image)  
    print ('Detected Document Text')
   
    # Create image showing bounding box/polygon the detected lines/text
    if doc.pages:
        page = doc.pages[0]
        for field in page.form.fields:
            if(field.key and field.value and "social security" in field.key.text.lower()):
                print("!!!FOUND SOCIAL!!!")
                x1 = field.value.geometry.boundingBox.left*width
                y1 = field.value.geometry.boundingBox.top*height-2
                x2 = x1 + (field.value.geometry.boundingBox.width*width) + 5
                y2 = y1 + (field.value.geometry.boundingBox.height*height) + 2

                draw.rectangle([x1, y1, x2, y2], fill="Black")
    for block in blocks:

        DisplayBlockInformation(block)
             
        draw=ImageDraw.Draw(image)

        # if block['BlockType'] == "KEY_VALUE_SET":
        #     if block['EntityTypes'][0] == "KEY":
        #         ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height,'red')
        #     else:
        #         ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height,'green')  
            
        # if block['BlockType'] == 'LINE':
        #     ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height, 'blue')

        # if block['BlockType'] == 'WORD':
        #     ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height, 'red')
        # if 'Confidence' in block:
        #     if block['BlockType'] == 'WORD':
        #         if block['Confidence'] <= 85:
        #             ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height, 'red') 
        #         elif 85 <= block['Confidence'] <= 98:
        #             ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height, 'yellow')  
        #         elif block['Confidence'] > 98:
        #             ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height, 'green') 

        for block in blocks:
            if block['BlockType'] == "KEY_VALUE_SET":
                if 'KEY' in block['EntityTypes']:
                    ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height, 'red') 
                    
                else:
                    ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height, 'blue') 
            # uncomment to draw polygon for all Blocks
            points=[]
            # for polygon in block['Geometry']['Polygon']:
            #    points.append((width * polygon['X'], height * polygon['Y']))
            # draw.polygon((points), outline='blue')
            
            
    # Display the image
    image.show()
    return len(blocks)


def main():

    bucket = 'mg-textract-bucket'
    document = '2017_Form_W-2.png'
    block_count=process_text_analysis(bucket,document)
    print("Blocks detected: " + str(block_count))
    
if __name__ == "__main__":
    main()
