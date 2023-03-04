from tkinter import ttk
import tkinter as tk
import database as db
import tkcalendar as tkcal 
from datetime import datetime
import datetime as dt
import calendar
import traceback
import pandas
import datetime as dt
import pyperclip
import json
import os

with open('lotSize.json') as f:
    LOT_SIZES = json.load(f)
today = datetime.today().strftime("%Y-%m-%d")
print(today)
db.connect_to_sqlite(db.update_data, today)

root = tk.Tk()
root.title("Beta Calculator")

LAST_UPDATED = db.connect_to_sqlite(db.get_last_date, "NIFTY50")

class FilteredBeta(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master=master)
        self.title("Filtered Stocks")

        self.status_var = tk.StringVar()
        self.status_lab = tk.Label(self, textvariable=self.status_var, font=('Helvetica', 13))
        self.status_lab.pack(pady=5)

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
        self.tv.heading(3, text='Beta (β)')
        self.frame_controls = tk.Frame(self.frame_top)
        self.frame_controls.pack(padx=5)

        self.delta_lab = tk.Label(self.frame_controls, text='No. of Days: ', font=('Helvetica', 13))
        self.delta_var = tk.StringVar(value="20")
        self.delta = ttk.Entry(self.frame_controls, textvariable=self.delta_var, width=7)
        self.delta.grid(row=1, column=0, padx=20)
        self.delta_lab.grid(row=0, column=0, padx=20)

        self.from_cal_lab = tk.Label(self.frame_controls, text='From: ', font=('Helvetica', 13))
        self.from_cal_var = tk.StringVar(value="30")
        self.from_cal = ttk.Entry(self.frame_controls, textvariable=self.from_cal_var, width=7)
        self.from_cal.grid(row=1, column=1, padx=20)
        self.from_cal_lab.grid(row=0, column=1, padx=20)

        self.to_cal_lab = tk.Label(self.frame_controls, text='To: ', font=('Helvetica', 13))
        self.to_cal = tkcal.DateEntry(self.frame_controls, selectmode='day')
        self.to_cal_lab.grid(row=0, column=2, padx=20)
        self.to_cal.grid(row=1, column=2, padx=20)

        self.ext_cal_lab = tk.Label(self.frame_controls, text='Extra: ', font=('Helvetica', 13))
        self.ext_cal = tkcal.DateEntry(self.frame_controls, selectmode='day')
        self.ext_cal_lab.grid(row=0, column=3, padx=20)
        self.ext_cal.grid(row=1, column=3, padx=20)

        self.ranks_lab = tk.Label(self.frame_controls, text='Ranks: ', font=('Helvetica', 13))
        self.ranks_var = tk.StringVar(value="5")
        self.ranks = ttk.Entry(self.frame_controls, textvariable=self.ranks_var, width=7)
        self.ranks.grid(row=1, column=4, padx=20)
        self.ranks_lab.grid(row=0, column=4, padx=20)

        self.button = ttk.Button(self.frame_controls, text="Calculate", command=self.show)
        self.button.grid(row=0, column=5, padx=20, rowspan=2)
        self.export_button = ttk.Button(self, text="Export", command=self.export)
        self.export_button.pack(pady=15)

    def status(self, msg="", color="black"):
        self.status_var.set(msg)
        self.status_lab.config(fg=color)
        self.update()
    
    def export(self):
        self.status("Exporting...")
        try:
            result = self.filtered()
            with open("data5.csv", "w", newline="") as f:
                f.write(f"Date,Stock,Lotsize\n")
                for i in result[1]:
                    f.write(f"{i[0].strftime('%d-%m-%Y')},{i[1]},{LOT_SIZES[i[1]]}\n")
            os.startfile('data5.csv')
            self.status(f"Exported results from {result[2]} to {result[3]}", "green")
        except Exception as e:
            print(traceback.format_exc())
            self.status("Something went wrong", "red")

    def show(self):
        self.status("Computing...")
        try:
            for i in self.tv.get_children():
                self.tv.delete(i)
            result = self.filtered()
            if not result:
                self.status("Extra Date Invalid", "red")
                return
            for i,row in enumerate(result[0]):
                self.tv.insert(parent='', index=i, iid=i, values=row)
            self.status(f"Showing results from {result[2]} to {result[3]}", "green")
        except Exception as e:
            print(traceback.format_exc())
            self.status("Something went wrong", "red")
        

    def filtered(self):
        DATA = []
        stocks_list = []
        ranks = int(self.ranks_var.get())
        date = pandas.Timestamp(self.to_cal.get_date())
        start = int(self.from_cal_var.get())
        count = 0
        temp_date = date
        while count < start:
            temp_date = temp_date - dt.timedelta(days=1)
            if temp_date.weekday() < 5:
                count += 1
        from_date = pandas.Timestamp(temp_date)
        delta = int(self.delta_var.get())
        extra = self.ext_cal.get_date()
        if extra > from_date:
            return None

        dates_of_month = [pandas.Timestamp(extra)] + list(pandas.date_range(from_date, date))
        export_exclude = []
        for dat in dates_of_month:
            if dat >= date:
                break
            data = calc(show=False, end=dat, days_delta=delta, sort='htl')[:ranks]
            if dat != extra:
                for i in data:
                    if i['Symbol'] not in [x[1] for x in stocks_list] and i["Symbol"] not in [x[1] for x in export_exclude]:
                        stocks_list.append([dat, i['Symbol']])
                        
            else:
                for i in data:
                    export_exclude.append([dat, i['Symbol']])

        data = calc(show=False, end=dat, days_delta=delta, sort='htl')[:ranks]
        print(stocks_list)
        
        for row in data:
            if row["Symbol"] not in [x[1] for x in stocks_list] and row["Symbol"] not in [x[1] for x in export_exclude]:
                DATA.append((row["Symbol"], row["Sector"], round(row["Beta"], 2)))
                stocks_list.append([dat, row["Symbol"]])
                
        
        return DATA, stocks_list, from_date.strftime("%d-%m-%Y"), date.strftime("%d-%m-%Y")

new_button = ttk.Button(root, text="NEW FILTER", command=lambda : FilteredBeta(root))
new_button.pack(pady=2)

Last_updated_lab = tk.Label(root, text="Last Updated: "+ LAST_UPDATED, font=("Helvetica", 13))
Last_updated_lab.pack()

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
    columns=(1, 2, 3), 
    show='headings', 
    height=7)
tv.pack()

tv.heading(1, text='Security')
tv.heading(2, text='Sector')
tv.heading(3, text='Beta (β)')

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
    string = f"{tv.item(cur_row)['values'][0]},{tv.item(cur_row)['values'][2]}"
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
        f.write("Scripts\n")
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
            data = calc(show=False, end=dat, days_delta=int(from_cal_var.get()), sort='htl')[:int(export_rows_var.get())]
            
            for i in data:
                DATA.append([dat.strftime('%d-%b-%Y'), i['Symbol'], str(i['Beta']), LOT_SIZES[i['Symbol']]])

    
    with open("data3.csv", "w", newline="") as f:
        f.write("Date,Stock,Beta,Lotsize\n")
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
from_cal_var = tk.StringVar(value="20")
from_cal = ttk.Entry(frame_controls, textvariable=from_cal_var)
from_cal.grid(row=1, column=1, padx=20)
from_cal_lab.grid(row=0, column=1, padx=20)

to_cal_lab = tk.Label(frame_controls, text='Last Date: ', font=('Helvetica', 13))
to_cal = tkcal.DateEntry(frame_controls, selectmode='day')
to_cal_lab.grid(row=0, column=2, padx=20)
to_cal.grid(row=1, column=2, padx=20)



def calc(sort=None, sectors=None, end=None, days_delta=None, show=True):
    for i in tv.get_children():
        tv.delete(i)
    
    if not end:        
        end = to_cal.get_date()
    if end.weekday() == 0:
        end = end - dt.timedelta(days=3)
    else:
        end = end - dt.timedelta(days=1)

    if not days_delta:        
        days_delta = int(from_cal.get())
        print(days_delta)
    count = 0
    temp_date = end
    while count < days_delta - 1:
        temp_day = temp_date.strftime("%A")
        if temp_day not in ["Saturday", "Sunday"]:
            count += 1
        temp_date = temp_date - dt.timedelta(days=1)
        
        
    start = temp_date.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d") 
    
    result = db.connect_to_sqlite(db.get_beta_and_sector, start, end)
    if sort == "htl":
        result = sorted(result, key=lambda data: data['Beta'], reverse=True)
    elif sort == "lth":
        result = sorted(result, key=lambda data: data['Beta'])
    elif sort == "sctr":
        sub_results = {}
        sorted_by_sector = []
        for i in result:
            if i["Sector"] in sectors:
                try:
                    sub_results[i["Sector"]].append(i)
                except KeyError:
                    sub_results[i["Sector"]] = []
                    sub_results[i["Sector"]].append(i)
        show_rows_val = int(show_rows_var.get())
        for v in sub_results.values():
            sub_sorted = sorted(list(v), key=lambda x: x["Beta"], reverse=True)
            if len(sub_sorted) > show_rows_val:
                sub_sorted = sub_sorted[:show_rows_val]
            for i in sub_sorted:
                sorted_by_sector.append(i)
        result = sorted_by_sector
                

    if show:
        for i,row in enumerate(result):
            tv.insert(parent='', index=i, iid=i, values=(row["Symbol"], row["Sector"], round(row["Beta"], 2)))
    else:
        return result


button = ttk.Button(frame_controls, text="Calculate", command=calc)
button.grid(row=0, column=3, padx=20, rowspan=2)


selected = tk.StringVar()
def sort_beta():
    order = selected.get()
    calc(sort=order)
r1 = ttk.Radiobutton(frame_controls, text='β high to low', value='htl', variable=selected, command=sort_beta)
r1.grid(row=0, column=0)
r2 = ttk.Radiobutton(frame_controls, text='β low to high', value='lth', variable=selected, command=sort_beta)
r2.grid(row=1, column=0)

checkbox_frame = tk.Frame(root)
checkbox_frame.pack(padx=5, pady=5)
sectors_raw = db.get_sector_info()
SECTORS = list(set(sectors_raw.values()))
checkbutton_vars = {}
column = 0
row = 0
def sort_sector():
    req_sectors = []
    for i,j in checkbutton_vars.items():
        if j.get() == "1":
            req_sectors.append(i)
    calc(sort="sctr", sectors=req_sectors)
    

for i, sector in enumerate(SECTORS):
    if i == 7:
        column = 1
        row = 0
    checkbutton_vars[sector] = tk.Variable()
    l = ttk.Checkbutton(checkbox_frame, text=sector, variable=checkbutton_vars[sector], command=sort_sector)
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
