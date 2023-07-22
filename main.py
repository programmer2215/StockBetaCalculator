from tkinter import ttk
import tkinter as tk
import oldDatabase as db
import tkcalendar as tkcal 
from datetime import datetime
from nsepython import nse_holidays
from database import get_last_date, update_data
import datetime as dt
from datetime import datetime as dt_
import calendar
import traceback
import pandas
import pyperclip
import json
import os

with open('filter.txt') as f:
    SELECTED_STOCKS = [x.strip() for x in f]


DB_DATE_FORMAT = "%Y-%m-%d"
NSE_HOLIDAYS = ['26-Jan-2023', '18-Feb-2023', '19-Feb-2023', '07-Mar-2023', '22-Mar-2023', '30-Mar-2023', '01-Apr-2023', '04-Apr-2023', '07-Apr-2023', '14-Apr-2023', '22-Apr-2023', '01-May-2023', '05-May-2023', '28-Jun-2023', '29-Jul-2023', '15-Aug-2023', '16-Aug-2023', '19-Sep-2023', '28-Sep-2023', '02-Oct-2023', '24-Oct-2023', '12-Nov-2023', '14-Nov-2023', '27-Nov-2023', '25-Dec-2023']
#NSE_HOLIDAYS = [dt_.strptime(x['tradingDate'], "%d-%b-%Y").strftime("%d-%m-%Y") for x in nse_holidays()['CBM']]
NSE_HOLIDAYS = [dt_.strptime(x, "%d-%b-%Y").strftime("%d-%m") for x in NSE_HOLIDAYS]
print(NSE_HOLIDAYS) # <--- DD-MM-YYYY
with open('lotSize.json') as f:
    LOT_SIZES = json.load(f)
with open('stocks.txt') as f:
    STOCKS = [x.strip() for x in f]
today = datetime.today().strftime(DB_DATE_FORMAT)
print(today)
#db.update_data(today)
print(f'LAST UPDATED {get_last_date("NIFTY50")}')
if input("Do you want to update (y/n): ") == 'y':
    update_data(get_last_date("NIFTY50"))

root = tk.Tk()
root.title("Beta Calculator")

LAST_UPDATED = db.get_last_date("NIFTY50")



class PreOpenData(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master=master)
        self.title("Pre Open")
        
        self.status_var = tk.StringVar()
        self.status_lab = tk.Label(self, textvariable=self.status_var, font=('Helvetica', 13))
        self.status_lab.pack(pady=5)

        self.nifty_var = tk.StringVar()
        self.nifty_lab = tk.Label(self, textvariable=self.nifty_var, font=('Helvetica', 13))
        self.nifty_lab.pack(pady=5)

        self.frame_top = tk.Frame(self)
        self.frame_top.pack(padx=5, pady=5)

        self.tv = ttk.Treeview(
            self.frame_top, 
            columns=(1, 2, 3), 
            show='headings', 
            height=7)
        self.tv.pack()

        self.tv.heading(1, text='Security')
        self.tv.heading(2, text='Sector')
        self.tv.heading(3, text='Prc. Cng. %')
        self.frame_controls = tk.Frame(self.frame_top)
        self.frame_controls.pack(padx=5)

        self.selected = tk.StringVar()
        
        self.r1 = ttk.Radiobutton(self.frame_controls, text='high to low', value='htl', variable=self.selected)
        self.r1.grid(row=0, column=0)
        self.r2 = ttk.Radiobutton(self.frame_controls, text='low to high', value='lth', variable=self.selected,state='selected')
        self.r2.grid(row=1, column=0)

        self.selected.set("htl")

        

        self.date_cal_lab = tk.Label(self.frame_controls, text='To: ', font=('Helvetica', 13))
        self.date_cal = tkcal.DateEntry(self.frame_controls, selectmode='day')
        self.date_cal_lab.grid(row=0, column=1, padx=20)
        self.date_cal.grid(row=1, column=1, padx=20)

        self.button = ttk.Button(self.frame_controls, text="Show", command=self.show)
        self.button.grid(row=0, column=2, padx=20, rowspan=2)

        self.tv.bind("<Button-3>", self.my_popup)

        self.right_click_menu = tk.Menu(self.tv, tearoff=False)
        self.right_click_menu.add_command(label="Copy Security", command=self.copy_security)

    def show(self):
        for i in self.tv.get_children():
                self.tv.delete(i)
        date = self.date_cal.get_date().strftime(DB_DATE_FORMAT)
        DATA, nifty = db.fetch_preopen(date, sort=self.selected.get())
        for i,row in enumerate(DATA):
            self.tv.insert(parent='', index=i, iid=i, values=row)
        self.nifty_var.set(f"Nifty : {round(nifty, 3)} %")
        if nifty < 0:
            self.nifty_lab.config(fg="red")
        else:
            self.nifty_lab.config(fg="green")
    
    def copy_security(self):
        cur_row = self.tv.focus()
        pyperclip.copy(self.tv.item(cur_row)['values'][0])

    def my_popup(self, e):
        self.right_click_menu.tk_popup(e.x_root, e.y_root)
        
        
but_frame = tk.Frame(root)
but_frame.pack()
new_button = ttk.Button(but_frame, text="PRE OPEN", command=lambda : PreOpenData(root))
new_button.grid(row=0, column=0, pady=2)

class FilteredBeta(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master=master)
        self.title("Filtered Stocks")

        self.status_var = tk.StringVar()
        self.status_lab = tk.Label(self, textvariable=self.status_var, font=('Helvetica', 13))
        self.status_lab.pack(pady=5)

        
        self.frame_controls = tk.Frame(self)
        self.frame_controls.pack(padx=5, pady=20)

        self.delta_lab = tk.Label(self.frame_controls, text='No. of Days: ', font=('Helvetica', 13))
        self.delta_var = tk.StringVar(value="5")
        self.delta = ttk.Entry(self.frame_controls, textvariable=self.delta_var, width=7)
        self.delta.grid(row=1, column=0, padx=20)
        self.delta_lab.grid(row=0, column=0, padx=20)

        self.from_cal_lab = tk.Label(self.frame_controls, text='From: ', font=('Helvetica', 13))
        self.from_cal = tkcal.DateEntry(self.frame_controls, selectmode='day')
        self.from_cal_lab.grid(row=0, column=1, padx=20)
        self.from_cal.grid(row=1, column=1, padx=20)

        self.to_cal_lab = tk.Label(self.frame_controls, text='To: ', font=('Helvetica', 13))
        self.to_cal = tkcal.DateEntry(self.frame_controls, selectmode='day')
        self.to_cal_lab.grid(row=0, column=2, padx=20)
        self.to_cal.grid(row=1, column=2, padx=20)


        self.ranks_lab = tk.Label(self.frame_controls, text='Ranks: ', font=('Helvetica', 13))
        self.ranks_var = tk.StringVar(value="1")
        self.ranks = ttk.Entry(self.frame_controls, textvariable=self.ranks_var, width=7)
        self.ranks.grid(row=1, column=4, padx=20)
        self.ranks_lab.grid(row=0, column=4, padx=20)

        self.monthly_export_button = ttk.Button(self.frame_controls, text="Monthly Export", command=self.but_export_monthly)
        self.monthly_export_button.grid(row=0, column=5, padx=20, rowspan=2)

        
        
    def status(self, msg="", color="black"):
        self.status_var.set(msg)
        self.status_lab.config(fg=color)
        self.update()
    


    def but_export_monthly(self):
    
        DATA = []
        
        start_date = self.from_cal.get_date()
        end_date = self.to_cal.get_date()
        days_delta = int(self.delta_var.get())
        ranks = int(self.ranks_var.get())
        td = dt.timedelta(days=1)

        curdate = start_date
        while curdate <= end_date:
            if curdate.weekday() < 5 and curdate.strftime("%d-%m") not in NSE_HOLIDAYS:
                data, low_cpr = calc(display=False, end=curdate, days_delta=days_delta, sort='cprβ', show_movement=True, show_low_cpr=True)
                data = data[:ranks]
                for i in data:
                    i['Date'] = curdate.strftime("%d-%m-%Y")
                    i['Lotsize'] = LOT_SIZES[i['Symbol']]
                    i['LowCPR'] = low_cpr['Symbol']
                    
                    DATA.append(i)
            curdate = curdate + td
        
        

        
        with open("filtered_data.csv", "w", newline="") as f:
            f.write("Date,Stock,Movement, Movement %,Lotsize,Low CPR\n")
            for i in DATA:
                f.write(f"{i['Date']},{i['Symbol']},{i['Movement']},{i['MovementPer']},{i['Lotsize']},{i['LowCPR']}\n")
                
        os.startfile('filtered_data.csv')
        

    

new_button = ttk.Button(but_frame, text="NEW FILTER", command=lambda : FilteredBeta(root))
new_button.grid(row=0, column=1, padx=10)

Last_updated_lab = tk.Label(root, text="Last Updated: "+ LAST_UPDATED, font=("Helvetica", 13))
Last_updated_lab.pack()

low_cpr_var = tk.StringVar(root)
low_cpr_lab = tk.Label(root, textvariable=low_cpr_var, font=("Helvetica", 13))
low_cpr_lab.pack()

style = ttk.Style()
style.configure("Treeview", font=('Britannic', 11, 'bold'), rowheight=25)
style.configure("Treeview.Heading", font=('Britannic' ,13, 'bold'))

# Tkinter Bug Work Around
if root.getvar('tk_patchLevel')=='8.6.9': #and OS_Name=='nt':
    def fixed_map(option):
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.
        #
        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        return [elm for elm in style.map('Treeview', query_opt=option) if elm[:2] != ('!disabled', '!selected')]
    style.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))


frame_top = tk.Frame(root)
frame_top.pack(padx=5, pady=5)

tv = ttk.Treeview(
    frame_top, 
    columns=(1, 2, 3, 4), 
    show='headings', 
    height=5)
tv.pack()

tv.column("#1", width=130)
tv.column("#2", width=190)
tv.column("#3", width=90)
tv.column("#4", width=90)

tv.heading(1, text='Security')
tv.heading(2, text='Sector')
tv.heading(3, text='Beta (β)')
tv.heading(4, text='CPR')

def copy_security():
    cur_row = tv.focus()
    pyperclip.copy(tv.item(cur_row)['values'][0])

def copy_beta():
    cur_row = tv.focus()
    pyperclip.copy(tv.item(cur_row)['values'][2])

def copy_open():
    cur_row = tv.focus()
    pyperclip.copy(tv.item(cur_row)['values'][1])

def copy_row():
    cur_row = tv.focus()
    string = f"{tv.item(cur_row)['values'][0]},{tv.item(cur_row)['values'][2]},{tv.item(cur_row)['values'][3]}"
    pyperclip.copy(string)

def export():
    
    with open("data.csv", "w", newline="") as f:
        for i in tv.get_children():
            data = tv.item(i)['values']
            f.write(f"{data[0]},{data[1]},{data[2]}")
            f.write("\n")
    os.startfile('data.csv')

def but_export():
    with open("data2.csv", "w", newline="") as f:
        f.write("Scripts,Lot Size\n")
        for i in tv.get_children()[:4]:
            data = tv.item(i)['values']
            lot_size = LOT_SIZES[data[0]]
            f.write(f"{data[0]},{lot_size}\n")
            
    os.startfile('data2.csv')

def but_export_monthly():
    
    DATA = []
    date = to_cal.get_date()
    num_days = calendar.monthrange(date.year, date.month)[1]
    dates_of_month = [dt.date(date.year, date.month, day) for day in range(1, num_days+1)] 
    for dat in dates_of_month:
        if dat > date:
            break
        if dat.month == date.month and dat.weekday() < 5:
            data = calc(display=False, end=dat, days_delta=int(from_cal_var.get()), sort='htl')[0]
            DATA.append([dat.strftime('%d-%b-%Y'), "Beta", data['Symbol'], LOT_SIZES[data['Symbol']]])
            _, low = calc(display=False, end=dat, days_delta=int(from_cal_var.get()), sort='htl', show_low_cpr=True)
            DATA.append([dat.strftime('%d-%b-%Y'), "CPR", low['Symbol'], LOT_SIZES[low['Symbol']]])

    
    with open("data3.csv", "w", newline="") as f:
        f.write("Date,Sort Type,Stock,Lotsize\n")
        for i in DATA:
            f.write(f"{','.join(i)}\n")
            
    os.startfile('data3.csv')

def my_popup(e):
    right_click_menu.tk_popup(e.x_root, e.y_root)

tv.bind("<Button-3>", my_popup)

right_click_menu = tk.Menu(tv, tearoff=False)
right_click_menu.add_command(label="Copy Security", command=copy_security)
right_click_menu.add_command(label="Copy Beta Value", command=copy_beta)
right_click_menu.add_command(label="Copy Open Price Value", command=copy_open)
right_click_menu.add_command(label="Copy Row", command=copy_row)
right_click_menu.add_command(label="Export to Excel", command=export)

frame_controls = tk.Frame(frame_top)
frame_controls.pack(padx=5)

from_cal_lab = tk.Label(frame_controls, text='No. of Days: ', font=('Helvetica', 13))
from_cal_var = tk.StringVar(value="5")
from_cal = ttk.Entry(frame_controls, textvariable=from_cal_var)
from_cal.grid(row=1, column=2, padx=20)
from_cal_lab.grid(row=0, column=2, padx=20)

to_cal_lab = tk.Label(frame_controls, text='Last Date: ', font=('Helvetica', 13))
to_cal = tkcal.DateEntry(frame_controls, selectmode='day')
to_cal_lab.grid(row=0, column=3, padx=20)
to_cal.grid(row=1, column=3, padx=20)



def calc(
        sort=None, 
        stocks=None, 
        end=None, 
        days_delta=None, 
        display=True, 
        cpr_date=None,
        show_movement=False,
        show_low_cpr = False,
        ):
    
    global SELECTED_STOCKS

    for i in tv.get_children():
        tv.delete(i)
    
    if not end:        
        end = to_cal.get_date()
    actual_date = end.strftime("%Y-%m-%d")
        
    

    if not days_delta:        
        days_delta = int(from_cal.get())
        print(days_delta)
    count = 0
    temp_date = end
    
    while count < days_delta:
        temp_date = temp_date - dt.timedelta(days=1)
        temp_day = temp_date.strftime("%A")
        if temp_day not in ["Saturday", "Sunday"] and temp_date.strftime('%d-%m') not in NSE_HOLIDAYS:
            if  not cpr_date:
                cpr_date = temp_date
                true_end = temp_date
            count += 1
        
        
        
    start = temp_date.strftime(DB_DATE_FORMAT)
    end = true_end.strftime(DB_DATE_FORMAT) 
    cpr_date = cpr_date.strftime(DB_DATE_FORMAT)
    print(start, end)
    
    result = db.get_beta_and_sector(start, end, cpr_date=cpr_date, show_movement=show_movement, act_date=actual_date)
    if SELECTED_STOCKS:
        result = [x for x in result if x['Symbol'] in SELECTED_STOCKS]
    
    low_cpr = sorted(result, key=lambda data: data['CPR'])[0]
    if display:
        low_cpr_var.set(f"Low CPR: {low_cpr['CPR']} ({low_cpr['Symbol']})")
    if sort == "htl":
        result = sorted(result, key=lambda data: data['Beta'], reverse=True)
    elif sort == "lth":
        result = sorted(result, key=lambda data: data['Beta'])
    
    elif sort == "βcpr":
        result = sorted(result, key=lambda data: data['Beta'], reverse=True)[:5]
        result = sorted(result, key=lambda data: data['CPR'])
    elif sort == "cprβ":
        result = sorted(result, key=lambda data: data['CPR'])[:5]
        result = sorted(result, key=lambda data: data['Beta'], reverse=True)
    elif sort == "sym":
        
        result = [x for x in result if x['Symbol'] in stocks]
                

    if display:
        for i,row in enumerate(result):
            tv.insert(parent='', index=i, iid=i, values=(row["Symbol"], row["Sector"], round(row["Beta"], 2), row['CPR']))
    else:
        if show_low_cpr:
            return result, low_cpr
        else:
            return result


button = ttk.Button(frame_controls, text="Calculate", command=calc)
button.grid(row=0, column=4, padx=20, rowspan=2)


selected = tk.StringVar()
def sort_beta():
    order = selected.get()
    calc(sort=order)
r1 = ttk.Radiobutton(frame_controls, text='β high to low', value='htl', variable=selected, command=sort_beta)
r1.grid(row=0, column=0)
r2 = ttk.Radiobutton(frame_controls, text='β low to high', value='lth', variable=selected, command=sort_beta)
r2.grid(row=1, column=0)
r3 = ttk.Radiobutton(frame_controls, text='β -> CPR', value='βcpr', variable=selected, command=sort_beta)
r3.grid(row=0, column=1)

r4 = ttk.Radiobutton(frame_controls, text='CPR -> β', value='cprβ', variable=selected, command=sort_beta)
r4.grid(row=1, column=1)

checkbox_frame = tk.Frame(root)
checkbox_frame.pack(padx=5, pady=5)
sectors_raw = db.get_sector_info()
SECTORS = list(set(sectors_raw.values()))
checkbutton_vars = {}
column = 0
row = 0


def save_filter(data):
    with open("filter.txt", "w") as f:
        for i in data:
            f.write(i + "\n")

def sort_stock():
    global SELECTED_STOCKS
    SELECTED_STOCKS = []
    for i,j in checkbutton_vars.items():
        if j.get() == "1":
            SELECTED_STOCKS.append(i)

    save_filter(SELECTED_STOCKS)
    calc(sort="sym", stocks=SELECTED_STOCKS)



def sort_all_sector():
    
    if checkbutton_vars['all'] != "1":
        for _, j in checkbutton_vars.items():
            j.set("1")
            
    else:
        for _, j in checkbutton_vars.items():
            j.set("0")
    sort_stock()

for i, stock in enumerate(STOCKS):
    if i % 7 == 0:
        column += 1
        row = 0
    checkbutton_vars[stock] = tk.Variable()
    if stock in SELECTED_STOCKS:
        checkbutton_vars[stock].set("1")
    l = ttk.Checkbutton(checkbox_frame, text=stock, variable=checkbutton_vars[stock], command=sort_stock)
    l.grid(column=column, row=row, padx=5, sticky=tk.W)
    row += 1
export_frame = tk.Frame(root)
export_frame.pack(pady= 3)

show_rows_lab = tk.Label(export_frame, text="Show Rows:")
show_rows_lab.grid(row=0, column=0 , padx=5)
show_rows_var = tk.StringVar(value="1")
show_rows = ttk.Entry(export_frame, textvariable=show_rows_var)
show_rows.grid(row=1, column=0 , padx=5)

export_button = ttk.Button(export_frame, text="Export", command=but_export)
export_button.grid(row=2, column=0 , padx=5)

export_rows_lab = tk.Label(export_frame, text="Show Rows:")
export_rows_lab.grid(row=0, column=1, padx=10)
export_rows_var = tk.StringVar(value="5")
export_rows = ttk.Entry(export_frame, textvariable=export_rows_var)
export_rows.grid(row=1, column=1, padx=40)
export_button_mon = ttk.Button(export_frame, text="Export Results For Month", command=but_export_monthly)
export_button_mon.grid(row=2, column=1)
root.mainloop()