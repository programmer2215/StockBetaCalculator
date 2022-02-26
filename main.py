from tkinter import ttk
import tkinter as tk
import database as db
import tkcalendar as tkcal 
from datetime import datetime
import datetime as dt

today = datetime.today().strftime("%Y-%m-%d")
print(today)
db.connect_to_sqlite(db.update_data, today)

root = tk.Tk()
root.title("Beta Calculator")

LAST_UPDATED = db.connect_to_sqlite(db.get_last_date, "NIFTY50")

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
frame_top.pack(padx=5, pady=20)

tv = ttk.Treeview(
    frame_top, 
    columns=(1, 2, 3), 
    show='headings', 
    height=10)
tv.pack()

tv.heading(1, text='Security')
tv.heading(2, text='Sector')
tv.heading(3, text='Beta (β)')

frame_controls = tk.Frame(frame_top)
frame_controls.pack(padx=5, pady=10)

from_cal_lab = tk.Label(frame_controls, text='No. of Days: ', font=('Helvetica', 13))
from_cal_var = tk.StringVar(value="10")
from_cal = ttk.Entry(frame_controls, textvariable=from_cal_var)
from_cal.grid(row=1, column=1, padx=20, pady=5)
from_cal_lab.grid(row=0, column=1, padx=20, pady=5)

to_cal_lab = tk.Label(frame_controls, text='Last Date: ', font=('Helvetica', 13))
to_cal = tkcal.DateEntry(frame_controls, selectmode='day')
to_cal_lab.grid(row=0, column=2, padx=20, pady=5)
to_cal.grid(row=1, column=2, padx=20, pady=5)



def calc(sort=None, sectors=None):
    for i in tv.get_children():
        tv.delete(i)
    
    end = to_cal.get_date()
    days_delta = int(from_cal.get())
    count = 0
    temp_date = end
    while count < days_delta:
        temp_date = temp_date - dt.timedelta(days=1)
        temp_day = temp_date.strftime("%A")
        if temp_day not in ["Saturday", "Sunday"]:
            count += 1
    start = temp_date.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")
    print(start, end)
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
                

    for i,row in enumerate(result):
        tv.insert(parent='', index=i, iid=i, values=(row["Symbol"], row["Sector"], round(row["Beta"], 2)))


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
show_row_frame = tk.Frame(root)
show_row_frame.pack(pady=10)

show_rows_lab = tk.Label(show_row_frame, text="Show Rows:")
show_rows_lab.pack()
show_rows_var = tk.StringVar(value="1")
show_rows = ttk.Entry(show_row_frame, textvariable=show_rows_var)
show_rows.pack()


root.mainloop()