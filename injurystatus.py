import requests
import lxml.html as lh
import pandas as pd
import re

class InjuryTable:
    def __init__(self, url='https://www.cbssports.com/nba/injuries/'):
        # Create a handle, page, to handle the contents of the website
        page = requests.get(url)
        # Store the contents of the website under doc
        doc = lh.fromstring(page.content)
        # Parse data that are stored between <tr>..</tr> of HTML
        tr_elements = doc.xpath('//tr')
        tr_elements = doc.xpath('//tr')

        # Create empty list
        col = []
        i = 0

        # For each row, store each first element (header) and an empty list
        for t in tr_elements[0]:
            i += 1
            name = t.text_content()
            # print('%d:"%s"'%(i,name.strip()))
            col.append((name.strip(),[]))
        # print(col)

        #Since out first row is the header, data is stored on the second row onwards
        for j in range(1,len(tr_elements)):
            #T is our j'th row
            T = tr_elements[j]

            #If row is not of size 5, the //tr data is not from our table
            if len(T) != 5:
                break

            #i is the index of our column
            i = 0

            #Iterate through each element of the row
            for t in T.iterchildren():
                data = t.text_content()
                #Modify first cell
                if i == 0:
                    #remove redundant headings
                    if data.strip() == 'Player':
                        break
                    #remove abbreviated name
                    else:
                        data = data.strip()
                        data = re.sub(r'.*\n', '\n', data)
                        data = data.strip()
                        if data == 'Moe Wagner':
                            data = 'Moritz Wagner'
                #Check if row is empty
                if i > 0:
                #Convert any numerical value to integers
                    try:
                        data = float(data.strip())
                    except:
                        pass
                #Append the data to the empty list of the i'th column
                col[i][1].append(data.strip())
                #Increment i for the next column
                i += 1
        self.col = col


    def addinjury(self, Player, Pos, UpdateDate, Injury, EndDate):
        self.col[0][1].append(Player)
        self.col[1][1].append(Pos)
        self.col[2][1].append(UpdateDate)
        self.col[3][1].append(Injury)
        self.col[4][1].append('Expected to be out until at least '+ EndDate)

    def addsuspension(self, Player, Pos, UpdateDate, EndDate):
        self.col[0][1].append(Player)
        self.col[1][1].append(Pos)
        self.col[2][1].append(UpdateDate)
        self.col[3][1].append('Suspension')
        self.col[4][1].append('Expected to be out until at least '+ EndDate)

    def databaseprint(self):
        Dict = {title:column for (title,column) in self.col}
        df = pd.DataFrame(Dict)
        df.to_excel("injurydata.xlsx")

    def editinjury(self, Player, Pos, UpdateDate, Injury, EndDate):
        if Player in self.col[0][1]:
            a = self.col[0][1].index(Player)
            (self.col[1][1])[a] = Pos
            (self.col[2][1])[a] = UpdateDate
            (self.col[3][1])[a] = Injury
            (self.col[4][1])[a] = 'Expected to be out until at least '+ EndDate
table = InjuryTable()

table.addsuspension('Deandre Ayton', 'C', 'Oct 28', 'Dec 17')
table.addsuspension('John Collins', 'PF', 'Nov 4', 'Dec 23')
table.databaseprint()
