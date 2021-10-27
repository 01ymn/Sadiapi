from logging import debug
from flask import Flask,request,jsonify,json,Response,make_response
import base64
from flask_cors import CORS
import re
from ocr_detection import *

#app_configuration :

app = Flask(__name__)
CORS(app)
app.config[debug] = True

#routing part :
@app.route('/',methods = ["GET","POST"])


def taritement():

    try :
        pdf = request.get_json()["PDF"]
    except:
        return jsonify({"message " : "No pdf sent"})
    try:
        with open("PDF_traiter.pdf","wb") as pdf_created:
            pdf_created.write(base64.b64decode(pdf))
    except:
        return jsonify({"message" : "error fichier format"})

    try :

        page = ai_formrecognizer("PDF_traiter.pdf")
        
        #variable_where we stock info_stock_info   
        name = ""
        Lines_check = 0
        Facture = ''
        Date_time = ''
        Num_client = ''
        réf_client = ""
        Total = ""
        uplines = ""

        #checking part : using regex :

        Date_time_regex = re.compile(r'^(\d{2}[/|.|-|*](\d{2}|[A-z][a-z][a-z])[/|.|-|*]\d{4}$)|(\d{2}\w\w\w\d{4})|(\d{2}[/|.|-|*]\d+[/|.|-|*]\d{4})')
        Facture_regex = re.compile(r'(\d+[\/]\d{2})|(\d+)|(\w+\d+)')
        Total_regex = re.compile(r'(\d+[\.]\d+[\,]\d+)|(\d+[\s]\d+[\,]+\d{2}[\s]\w+)||(\d+[\s]\d+[\,]+\d{2})')
        #Total_regex_Cat2 = re.compile(r'(\d+[\.]\d+[\,]\d+)|(\d+\s\d+[\,]+\d{2}[\s]\w+)|([\s]\d+[\s]\d+[\,]\d+)')
        Réf_regex = re.compile(r'\d+')

        #up_line function :

        def lines_up():
            for_Tab = {}
            Tab_Num = []
            Tab_content = []
            for idx, content in enumerate(page):
                for line_idx, line in enumerate(content.lines):
                    Tab_Num.append(line_idx)
                    Tab_content.append(line.text)
                    for I in range(len(Tab_Num)):
                        for_Tab[Tab_Num[I]] = Tab_content[I]
            return for_Tab

        #upline varuable : category One 
        uplines = lines_up()

        def tableau_extraction():
            List_column = []
            List_row = []
            all_table = []
            header=[]
            newl={}
            newr=[]
            newall=[]
            for table in page[0].tables:
                for row_1 in range(table.row_count):
                    for cell in table.cells:
                        if row_1 == cell.row_index:
                            List_row.append(cell.text)
                    List_column.append(List_row)
                    List_row = []
                all_table.append(List_column)
                List_column =[]
            header=all_table[0][0]
            for tt in range(1,len(all_table[0])):
                for jj in range(len(all_table[0][tt])):
                    newl[header[jj]]=all_table[0][tt][jj]
        
                newr.append(newl)
                newl={}
            newall.append(newr)
            newr=[]
            
            
            return newall

        #Table variable :  category Two
        Table_using = tableau_extraction()

        def extract_text_text_only():
            Text_nolines = []
            words = page[0].lines
            for formline in words:
                our_spliting_text = formline.text.split()
                Text_nolines.append(our_spliting_text)
            return Text_nolines 

        #Splitting variable :  category Three
        Spitting_part = extract_text_text_only()

        #checking the type of invoices :
        def checking_lines ():
            global Lines_check_under 
            for Idx,value in list(uplines.items()):
                if "Date de la facture" in value or "DATE" in value or "Total (TTC)" in value:
                    Lines_check_under = 1
                if "Date de la facture : " in value or "DATE : " in value or "Total (TTC)" in value :
                    Lines_check_under = 0
            return Lines_check_under

        lines_check = checking_lines()

        #checking if there is more than one tables:

        # print(Spitting_part)
        # print('------------------------------------------------------------------------------------------------------')


        # print(Table_using)
        # print('------------------------------------------------------------------------------------------------------')


        # print(uplines)
        # print('------------------------------------------------------------------------------------------------------')

        #category _ 1 :

        if len(Table_using) >= 2 and Lines_check == 0 :
            for list_2 in tableau_extraction():
                for list_1 in list_2:
                    if list_1[0] == 'NUMÉRO DE FACTURE' or list_1[0] == "N° Facture" or list_1[0]== "Référence de la facture":
                        Facture = list_1[1]
                    if list_1[0] == "DATE" or list_1[0] == "Date de la facture" or list_1[0] == "Paiement dû":
                         Date_time = list_1[1]
                    if list_1[0] == 'LIEU DE FORMATION' or list_1[0] == "Numéro de BC":
                         Num_client = list_1[1]
                    if list_1[0] == "CLIENT" or list_1[0]=="Destinataire":
                         réf_client = list_1[1]
                    if list_1[0] == "Total (TTC)":
                        Total = list_1[1]
                        if Total_regex.match(Total):
                            Total = Total
                    else :
                        Total = "None"
        if Total == "None" :
            for index,content in uplines.items():
                if "Total (TTC)" in content:
                    Total = uplines[index+1]
                    if Total_regex.match(Total):
                        print(Total)
                    else:
                        Total = uplines[index]

        #category _ 2:

        if len(Table_using) <= 1  and checking_lines() == 0: 
            for J,Our_spitting in enumerate(Spitting_part):
                if Our_spitting[0] == 'Facture':
                    Facture = Our_spitting[-1]
                if Our_spitting[0] == "Date":
                    Date_time = Our_spitting[-1]
                    if Our_spitting[1] == 'de':
                        if Our_spitting[2] == "la":
                            if Our_spitting[3] == "facture":
                                Date_time = Our_spitting[-1]
                
                if Our_spitting[0] == 'Numéro':
                    if Our_spitting[1] == 'de':
                        if Our_spitting[2] == "client":
                            name = 'Numéro de client'
                            Num_client = Our_spitting[-1]
                if Our_spitting[0] =="Total":
                    if Our_spitting[1] == 'TTC':
                        Total = Our_spitting[-1]
                        if Total_regex.match(Total):
                            Total = Total
                        else :
                            Total = "None"
                if Total == "None" :
                    for index,content in uplines.items():
                        if "Total TTC" in content:
                            Total = uplines[index+1]
                            if Total_regex.match(Total):
                                Total = Total
                            else:
                                Total = uplines[index]
        
        #category _ 3 :
                        
        if len(Table_using) <= 1  and lines_check == 1:
            for index,content in uplines.items():
                if content == "Référence de la facture" or content == "Référence du devis" :
                    Facture = uplines[index+1]   
                if content == 'DATE' or content == "Date de la facture" or content == "Date d'émission du devis":
                    Date_time = uplines[index+1]
                if content == 'Numéro de client' or content == "CLIENT" or content == "Numéro de BC":
                    name = content
                    Num_client = uplines[index+1]
                if content == "Total TTC" or content == "Total " :
                    Total = uplines[index+1]
                elif "Total TTC " :
                    Total = uplines[index]
        #confidence part : using ReGEX

        def confidence(facture,datetime,num_client,total,référence):
            if Facture_regex.match(facture):
                facture = facture
            else:
                facture = ""
            if Date_time_regex.match(datetime):
                datetime = datetime
            else :
                datetime = ""
            if Réf_regex.match(num_client):
                num_client = num_client
            else :
                num_client = num_client
            if Total_regex.match(total):
                total = total
            else : 
                total = total[10:len(total)]
            #excepted case :

            if référence is not None:
                référence = référence
            else :
                référence = " Not - found in this invoice "

        #Json format to return :

            resultas = {
                "N° facture" : facture,
                "Date Facture" : datetime,
                "Client info"  : num_client,
                "référence client" : référence,
                "Total" : total
                }
            return resultas
        return jsonify({"resultats " : confidence(Facture,Date_time,Num_client,str(Total),réf_client), "mytab" : Table_using[0]})
    except:
        return jsonify({'message' : 'ocr nonFunctional'})
    #done

    #testing part :
    
    print("invoice info")
    print(confidence(Facture,Date_time,Num_client,str(Total)))
    print("")
    print(' * Tables : ')
    print("")
    print(Table_using)
