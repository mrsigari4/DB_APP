import os
import sys
import random
import pdfkit
import logging
import pandas as pd
import customtkinter
from PIL import Image
from tkinter import ttk
from VF import send_email
from datetime import datetime
from tkinter import filedialog
from tkcalendar import DateEntry
from database import connect_to_db
from KeyringAuthentication import LoginSetter, LoginGetter


conn = None
DATABASE_name = ''
SERVER_name = ''

log_directory = 'BD/Log'

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(filename='BD/Log/app.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
7
def Two_FA(username):
    global conn
    cursor = conn.cursor()
    cursor.execute(f"SELECT Email FROM Email_authorization WHERE Login = '{username}';")
    test = cursor.fetchall()
    emails = [row['Email'] for row in test if row['Email'].strip()]

    if not emails:
        logging.warning(f"No email found for user: {username}")
    else:
        for email in emails:
            logging.info(f"Email found for {username}")

    def generate_random_numbers():
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    CODE = generate_random_numbers()
    logging.info(f"Generated 2FA code for {username}")
    
    send_email(email, CODE)
    logging.info(f"Sent 2FA code to {email}")

    return CODE

def get_view_names_from_db():
    global conn
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES WHERE table_type = 'VIEW';")
    view_names = [row['table_name'] for row in cursor.fetchall()]
    logging.info("Fetched view names from the database")
    return view_names

def get_table_names_from_db():
    global conn
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES WHERE table_type = 'BASE TABLE';")
    table_names = [row['table_name'] for row in cursor.fetchall()]
    logging.info("Fetched table names from the database")
    return table_names

def get_stored_procedures_functions():
    global conn
    cursor = conn.cursor()
    cursor.execute("SELECT specific_name FROM information_schema.routines WHERE routine_type IN ('PROCEDURE', 'FUNCTION')")
    stored_procs_funcs = [row['specific_name'] for row in cursor.fetchall()]
    logging.info("Fetched stored procedures and functions from the database")
    return stored_procs_funcs

class CombinedApp(customtkinter.CTk):
    width = 1080
    height = 780
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results_dict = None
    
        self.title("DB App")
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)

        # load and create background image
        current_path = os.path.dirname(os.path.realpath(__file__))
        self.bg_image = customtkinter.CTkImage(Image.open(current_path + "/test_images/bg_gradient.jpg"),
                                               size=(self.width, self.height))
        self.bg_image_label = customtkinter.CTkLabel(self, image=self.bg_image)
        self.bg_image_label.grid(row=0, column=0)

        # create login frame
        self.login_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.login_frame.grid(row=0, column=0, sticky="ns")
        self.login_label = customtkinter.CTkLabel(self.login_frame, text="Data Base\nApplication",
                                                  font=customtkinter.CTkFont(size=20, weight="bold"))
        self.login_label.grid(row=0, column=0, padx=30, pady=(150, 15))
        self.username_entry = customtkinter.CTkEntry(self.login_frame, width=200, placeholder_text="Username")
        self.username_entry.grid(row=3, column=0, padx=30, pady=(15, 15))
        self.password_entry = customtkinter.CTkEntry(self.login_frame, width=200, show="*", placeholder_text="Password")
        self.password_entry.grid(row=4, column=0, padx=30, pady=(0, 15))
        self.login_button = customtkinter.CTkButton(self.login_frame, text="Login", command=self.login_event, width=200)
        self.login_button.grid(row=5, column=0, padx=30, pady=(15, 15))
        self.login_inf_label = customtkinter.CTkLabel(self.login_frame, text="")
        self.login_inf_label.grid(row=6, column=0, padx=30, pady=(15, 15))
        self.username_entryKA = customtkinter.CTkEntry(self.login_frame, width=200, placeholder_text="Saved username")
        self.username_entryKA.grid(row=7, column=0, padx=30, pady=(15, 15))
        self.login_buttonKA = customtkinter.CTkButton(self.login_frame, text="Login", command=self.login_eventKA, width=200)
        self.login_buttonKA.grid(row=8, column=0, padx=30, pady=(15, 15))
        self.login_inf_labelKA = customtkinter.CTkLabel(self.login_frame, text="")
        self.login_inf_labelKA.grid(row=9, column=0, padx=30, pady=(15, 15))
        
    def login_event(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        global conn, DATABASE_name, SERVER_name
        DATABASE_name = ''
        SERVER_name = ''
        conn = connect_to_db(SERVER_name, DATABASE_name, username, password)

        if not conn:
            self.login_inf_label.configure(text="Connection error\n Check input login or password", text_color="red")
            logging.error(f"Connection error for user: {username}")
        else:
            self.login_frame.grid_forget()
            self.withdraw() 
            CODE = Two_FA(username)
            dialog = customtkinter.CTkInputDialog(text="Input your code from Email", title="VF")
            input_code = dialog.get_input()
            if input_code == CODE:
                logging.info(f"User {username} logged in successfully.")
                LoginSetter(username, password)
                self.create_main_app()
            else:
                logging.error(f"Failed 2FA for user: {username}")
                conn.close()
                sys.exit(0)

    def login_eventKA(self):
        username = self.username_entryKA.get()
        password = LoginGetter(username)

        global conn, DATABASE_name, SERVER_name
        DATABASE_name = ''
        SERVER_name = ''
        conn = connect_to_db(SERVER_name, DATABASE_name, username, password)

        if not conn:
            self.login_inf_labelKA.configure(text="Connection error\n Login not found", text_color="red")
            logging.error(f"Saved login not found for user: {username}")
        else:
            self.login_frame.grid_forget()
            self.withdraw()
            logging.info(f"User {username} logged in successfully using saved credentials.")
            self.create_main_app()

    def create_main_app(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.deiconify()

        self.title("image_example.py")
        self.geometry("900x450")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_images")
        self.logo_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "logo.png")), size=(70, 70))
        self.home_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "write_dark.png")),
                                                 dark_image=Image.open(os.path.join(image_path, "write_light.png")), size=(20, 20))
        self.chat_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "table_dark.png")),
                                                 dark_image=Image.open(os.path.join(image_path, "table_light.png")), size=(20, 20))
        self.add_user_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "eye_dark.png")),
                                                     dark_image=Image.open(os.path.join(image_path, "eye_light.png")), size=(20, 20))
        self.admin_panel = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "home_dark.png")),
                                                       dark_image=Image.open(os.path.join(image_path, "home_light.png")), size=(20, 20))

        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="ew")
        self.navigation_frame.grid_columnconfigure(5, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="  Data base application", image=self.logo_image,
                                                             compound="left", font=customtkinter.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Query",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w", command=self.home_button_event)
        self.home_button.grid(row=0, column=1, padx=10, pady=10)

        self.frame_2_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Tables",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      image=self.chat_image, anchor="w", command=self.frame_2_button_event)
        self.frame_2_button.grid(row=0, column=2, padx=10, pady=10)

        self.frame_3_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Views",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      image=self.add_user_image, anchor="w", command=self.frame_3_button_event)
        self.frame_3_button.grid(row=0, column=3, padx=10, pady=10)

        self.admin_panel_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Admin panel",
                                                          fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                          image=self.admin_panel, anchor="w", command=self.admin_panel_button_event)
        self.admin_panel_button.grid(row=0, column=4, padx=10, pady=10)

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self.navigation_frame, values=["System", "Dark", "light"],
                                                                command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=0, column=5, padx=20, pady=20, sticky="e")


                # Query frame
        self.Query_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.Query_frame.grid(row=1, column=0, sticky="nsew")
        self.Query_frame.grid_columnconfigure(1, weight=1)
        self.Query_optionemenu = customtkinter.CTkOptionMenu(self.Query_frame, values=get_stored_procedures_functions(),
                                                             command=self.change_appearance_mode_event, width=750)
        self.Query_optionemenu.grid(row=1, column=0, padx=(60, 0), pady=50)
        self.Query_frame_button_1 = customtkinter.CTkButton(self.Query_frame, text="RUN", command=self.query)
        self.Query_frame_button_1.grid(row=5, column=0, padx=20, pady=10, sticky="n")
        self.query_status_label = customtkinter.CTkLabel(self.Query_frame, text="", font=customtkinter.CTkFont(size=12), fg_color="black")
        self.query_status_label.grid(row=7, column=0, pady=5, sticky="n")
        self.Query_optionemenu.configure(command=lambda selected_option: self.update_query_parameters(selected_option))
                

                # Table Frame
        self.Table_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.Table_frame.grid(row=1, column=0, sticky="nsew")
        self.Table_frame.grid_columnconfigure(1, weight=1)
        self.Tables_optionemenu = customtkinter.CTkOptionMenu(self.Table_frame, values=get_table_names_from_db(),
                                                              command=self.change_appearance_mode_event)
        self.Tables_optionemenu.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.TableShow_button = customtkinter.CTkButton(self.Table_frame, text="show", command=self.table_show_button_event)
        self.TableShow_button.grid(row=1, column=1, padx=(0, 20), pady=(10, 10))


                # View Frame
        self.View_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.View_frame.grid(row=1, column=0, sticky="nsew")
        self.View_frame.grid_columnconfigure(1, weight=1)
        self.Views_optionemenu = customtkinter.CTkOptionMenu(self.View_frame, values=get_view_names_from_db(),
                                                             command=self.change_appearance_mode_event)
        self.Views_optionemenu.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.ViewShow_button = customtkinter.CTkButton(self.View_frame, text="show", command=self.view_show_button_event)
        self.ViewShow_button.grid(row=1, column=1, padx=(0, 20), pady=(10, 10), sticky="e")

        self.View_export_frame = customtkinter.CTkFrame(self.View_frame)
        self.View_export_frame.grid(row=2, column=1, padx=(0, 0), pady=(0, 0), sticky="ne")
        self.Export_view_optionemenu = customtkinter.CTkOptionMenu(self.View_export_frame, values=get_view_names_from_db(),
                                                                   command=self.change_appearance_mode_event)
        self.Export_view_optionemenu.grid(row=0, column=0, padx=(10, 0), pady=(10, 10))
        self.export_format_optionmenu2 = customtkinter.CTkOptionMenu(self.View_export_frame, values=["PDF", "Excel"])
        self.export_format_optionmenu2.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.export_format_optionmenu2.set("PDF")
        self.Eport_table_button = customtkinter.CTkButton(self.View_export_frame, text="Export Table", command=self.export_view)
        self.Eport_table_button.grid(row=2, column=0, padx=20, pady=(10, 10))


                # Admin frame
        self.Admin_panel_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.Admin_panel_frame.grid(row=1, column=0, sticky="nsew")
        self.Admin_panel_frame.grid_columnconfigure(1, weight=1)


                #tabview tables opperation
        self.operation_with_tables = customtkinter.CTkTabview(master=self.Table_frame, width=250, height=950)
        self.operation_with_tables.grid(row=2, column=1, padx=(0, 0), pady=(0, 0), sticky="ne")
        self.operation_with_tables.add("Insert")
        self.operation_with_tables.add("Delete")
        self.operation_with_tables.add("Update")
        self.operation_with_tables.add("Export")
        self.operation_with_tables.tab("Insert").grid_columnconfigure(0, weight=1)
        self.operation_with_tables.tab("Delete").grid_columnconfigure(0, weight=1)
        self.operation_with_tables.tab("Update").grid_columnconfigure(0, weight=1)
        self.operation_with_tables.tab("Export").grid_columnconfigure(0, weight=1)
        
        self.insert_widgets = []
        self.Tables_optionemenu.bind("<Configure>", self.update_insert_widgets)

        self.Insert_status_lable = customtkinter.CTkLabel(self.operation_with_tables.tab("Insert"), text="", font=customtkinter.CTkFont(size=12), fg_color="black")
        self.Insert_status_lable.grid(row=99, column=0, pady=5, sticky="n")


        self.delete_option_menu = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Delete"),
                                                              values=[],
                                                              command=self.update_option_menu)
        self.delete_option_menu.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.delete_entry = customtkinter.CTkEntry(self.operation_with_tables.tab("Delete"), placeholder_text="Enter value for deletion")
        self.delete_entry.grid(row=1, column=0, padx=20, pady=(10, 10))

        self.delete_button = customtkinter.CTkButton(self.operation_with_tables.tab("Delete"), text="Delete", command=self.delete_button_event)
        self.delete_button.grid(row=2, column=0, padx=20, pady=(10, 10))

        self.Delete_status_lable = customtkinter.CTkLabel(self.operation_with_tables.tab("Delete"), text="", font=customtkinter.CTkFont(size=12), fg_color="black")
        self.Delete_status_lable.grid(row=8, column=0, pady=5, sticky="n")


        self.Update_column_optionmenu_condition = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Update"),
                                                              values=[],
                                                              command=self.update_option_menu)
        self.Update_column_optionmenu_condition.grid(row=0, column=0, padx=20, pady=(10, 10))

        self.condition = customtkinter.CTkEntry(self.operation_with_tables.tab("Update"), placeholder_text="Enter WHERE condition")
        self.condition.grid(row=1, column=0, padx=20, pady=(10, 10))

        self.Update_column_optionmenu = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Update"),
                                                              values=[],
                                                              command=self.update_option_menu)
        self.Update_column_optionmenu.grid(row=2, column=0, padx=20, pady=(10, 10))

        self.Update_value_entry = customtkinter.CTkEntry(self.operation_with_tables.tab("Update"), placeholder_text="Enter new value")
        self.Update_value_entry.grid(row=3, column=0, padx=20, pady=(10, 10))

        self.Update_button = customtkinter.CTkButton(self.operation_with_tables.tab("Update"), text="Update", command=self.update_button_event)
        self.Update_button.grid(row=4, column=0, padx=20, pady=(10, 10))

        self.Update_status_lable = customtkinter.CTkLabel(self.operation_with_tables.tab("Update"), text="", font=customtkinter.CTkFont(size=12), fg_color="black")
        self.Update_status_lable.grid(row=8, column=0, pady=5, sticky="n")


        self.Export_table_optionemenu = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Export"), values=get_table_names_from_db(),
                                                              command=self.change_appearance_mode_event)
        self.Export_table_optionemenu.grid(row=0, column=0, padx=20, pady=(10, 10))

        self.export_format_optionmenu = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Export"), values=["PDF", "Excel"])
        self.export_format_optionmenu.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.export_format_optionmenu.set("PDF")

        self.Eport_table_button = customtkinter.CTkButton(self.operation_with_tables.tab("Export"), text="Export Table", command=self.export_table)
        self.Eport_table_button.grid(row=2, column=0, padx=20, pady=(10, 10))

        self.Tables_optionemenu.configure(command=lambda selected_table: self.update_option_menu(selected_table))


        self.admin_panel_interface = customtkinter.CTkTabview(master=self.Admin_panel_frame, width=1920, height=980)
        self.admin_panel_interface.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="n")
        self.admin_panel_interface.add("audit")
        self.admin_panel_interface.add("users rules")
        self.admin_panel_interface.tab("users rules").grid_columnconfigure(0, weight=1)
        self.admin_panel_interface.tab("audit").grid_columnconfigure(0, weight=1)

        self.audit_buton = customtkinter.CTkButton(master= self.admin_panel_interface.tab("audit"), text="Show db audit", command=self.open_db_audit, width=20, height=10)
        self.audit_buton.pack(pady=1,padx=30)
        
        self.audit_db_label = customtkinter.CTkScrollableFrame(master= self.admin_panel_interface.tab("audit"), width=1500, height=390, orientation="vertical")
        self.audit_db_label.pack(pady = 10)

        self.audit_buton = customtkinter.CTkButton(master= self.admin_panel_interface.tab("audit"), text="Show server audit", command=self.open_server_audit, width=20, height=10)
        self.audit_buton.pack(pady=1,padx=30)
        
        self.audit_server_label = customtkinter.CTkScrollableFrame(master= self.admin_panel_interface.tab("audit"), width=1500, height=390, orientation="vertical")
        self.audit_server_label.pack(pady = 10)

        self.query_label_admin= customtkinter.CTkEntry(master= self.admin_panel_interface.tab("users rules"),width= 1200,placeholder_text="Query ")
        self.query_label_admin.pack(pady = 10)

        self.query_admin_button= customtkinter.CTkButton(master= self.admin_panel_interface.tab("users rules"),command=self.query_run,text="RUN")
        self.query_admin_button.pack(pady=5)

        self.query_label_admin_info= customtkinter.CTkLabel(master=self.admin_panel_interface.tab("users rules"),text="")
        self.query_label_admin_info.pack(pady=10)
        
        self.select_frame_by_name("Query")
        self.update()
        self.mainloop()

    def query_run(self):
        global conn
        cursor=conn.cursor()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(self.query_label_admin.get())
                self.query_label_admin_info.configure(text='query successfully', fg_color='green')
                conn.commit()
                cursor.close()
                logging.info("Query executed successfully")
            except Exception as e:
                self.query_label_admin_info.configure(text='query errore', fg_color='red')
                conn.rollback()
                cursor.close()
                logging.error("Error executing query")

    def open_db_audit(self):
        global conn
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT event_time,sequence_number,action_id,succeeded,session_server_principal_name,server_principal_name,client_ip,transaction_id,application_name FROM sys.fn_get_audit_file('F:\SQL\AUDIT\DB\*.sqlaudit', null , null);")
                result = cursor.fetchall()
                headers = [column[0] for column in cursor.description]
                self.clear_db_audit_display()
                for col, header in enumerate(headers):
                            header_label = customtkinter.CTkLabel(self.audit_db_label, text=header, font=("Arial", 10, "bold"))
                            header_label.grid(row=0, column=col, padx=10, pady=5)
                for row_idx, row in enumerate(result):
                        for col_idx, header in enumerate(headers):
                            cell_value = row[header]
                            cell_label = customtkinter.CTkLabel(self.audit_db_label, text=str(cell_value), font=("Arial", 10, "bold"))
                            cell_label.grid(row=row_idx + 1, column=col_idx, padx=10, pady=5)
                cursor.close()
                logging.info("DB audit data fetched successfully.")
            except Exception as e:
                logging.error("Error fetching DB audit data: %s", str(e))

    def open_server_audit(self):
        global conn
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT event_time,sequence_number,action_id,succeeded,session_server_principal_name,server_principal_name,client_ip,transaction_id,application_name FROM sys.fn_get_audit_file('F:\SQL\AUDIT\SERVER\*.sqlaudit', null , null);")
                result = cursor.fetchall()
                headers = [column[0] for column in cursor.description]
                self.clear_server_audit_display()
                for col, header in enumerate(headers):
                            header_label = customtkinter.CTkLabel(self.audit_server_label, text=header, font=("Arial", 10, "bold"))
                            header_label.grid(row=0, column=col, padx=10, pady=5)
                for row_idx, row in enumerate(result):
                        for col_idx, header in enumerate(headers):
                            cell_value = row[header]
                            cell_label = customtkinter.CTkLabel(self.audit_server_label, text=str(cell_value), font=("Arial", 10, "bold"))
                            cell_label.grid(row=row_idx + 1, column=col_idx, padx=10, pady=5)
                cursor.close()
                logging.info("Server audit data fetched successfully.")
            except Exception as e:
                logging.error("Error fetching server audit data: %s", str(e))

    def clear_db_audit_display(self):
        logging.info('Clearing audit DB display')
        for widget in self.audit_db_label.winfo_children():
            widget.destroy()

    def clear_server_audit_display(self):
        logging.info('Clearing server audit display')
        for widget in self.audit_server_label.winfo_children():
            widget.destroy()

    def update_insert_widgets(self, event):
        selected_table = self.Tables_optionemenu.get()
        logging.info(f'Updating insert widgets')

        for widget in self.insert_widgets:
            widget.destroy()

        if selected_table:
            columns = self.get_columns_for_table(selected_table)

            for col_idx, column in enumerate(columns):
                if not self.column_has_constraints(selected_table, column, ["IDENTITY"]):
                    entry = customtkinter.CTkEntry(self.operation_with_tables.tab("Insert"), placeholder_text=column)
                    entry.grid(row=col_idx, column=0, padx=20, pady=(20, 10))
                    self.insert_widgets.append(entry)

            insert_button = customtkinter.CTkButton(self.operation_with_tables.tab("Insert"), text="Insert",
                                                    command=self.insert_button_event)
            insert_button.grid(row=len(self.insert_widgets), column=0, padx=20, pady=(10, 10))
            self.insert_widgets.append(insert_button)

    def update_option_menu(self, selected_table):
        logging.info(f'Updating option menu')
        columns = self.get_columns_for_table(selected_table)

        if columns:
            if hasattr(self, 'delete_option_menu') and isinstance(self.delete_option_menu, customtkinter.CTkOptionMenu):
                self.delete_option_menu.destroy()

            self.delete_option_menu = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Delete"), values=columns)
            self.delete_option_menu.grid(row=0, column=0, padx=20, pady=(20, 10))
            self.delete_option_menu.set(columns[0])

            if hasattr(self, 'Update_column_optionmenu_condition') and isinstance(self.Update_column_optionmenu_condition, customtkinter.CTkOptionMenu):
                self.Update_column_optionmenu_condition.destroy()

            self.Update_column_optionmenu_condition = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Update"), values=columns)
            self.Update_column_optionmenu_condition.grid(row=0, column=0, padx=20, pady=(20, 10))
            self.Update_column_optionmenu_condition.set(columns[0])

            if hasattr(self, 'Update_column_optionmenu') and isinstance(self.Update_column_optionmenu, customtkinter.CTkOptionMenu):
                self.Update_column_optionmenu.destroy()

            # Create a new Update_column_optionmenu
            self.Update_column_optionmenu = customtkinter.CTkOptionMenu(self.operation_with_tables.tab("Update"), values=columns)
            self.Update_column_optionmenu.grid(row=2, column=0, padx=20, pady=(20, 10))
            self.Update_column_optionmenu.set(columns[0])
        else:
            if hasattr(self, 'delete_option_menu') and isinstance(self.delete_option_menu, customtkinter.CTkOptionMenu):
                self.delete_option_menu.destroy()

            if hasattr(self, 'Update_column_optionmenu_condition') and isinstance(self.Update_column_optionmenu_condition, customtkinter.CTkOptionMenu):
                self.Update_column_optionmenu_condition.destroy()

            if hasattr(self, 'Update_column_optionmenu') and isinstance(self.Update_column_optionmenu, customtkinter.CTkOptionMenu):
                self.Update_column_optionmenu.destroy()

    def insert_button_event(self): #####
        cursor = conn.cursor()
        selected_table = self.Tables_optionemenu.get()
        logging.info(f'Insert operation started')

        if selected_table:
            non_identity_columns = [column for column in self.get_columns_for_table(selected_table)
                                    if not self.column_has_constraints(selected_table, column, ["IDENTITY"])]
            try:
                values = [entry.get() for entry in self.insert_widgets if isinstance(entry, customtkinter.CTkEntry)]

                values = [value for value in values if value]
            
                if values:
                    columns_str = ", ".join(non_identity_columns)
                    values_str = ", ".join(["%s" for _ in non_identity_columns])
                    insert_query = f"INSERT INTO {selected_table} ({columns_str}) VALUES ({values_str});"
                    logging.info(f'Executing query')

                    cursor.execute(insert_query, tuple(values))
                    conn.commit()
                    self.Insert_status_lable.configure(text='Insertion successful', fg_color='green')
                    self.table_show_button_event()
                    cursor.close()
                else:
                    logging.warning('Insertion failed: no values provided')
                    self.Insert_status_lable.configure(text='Fill in at least one field for insertion', fg_color='red')
                    conn.rollback()
                    cursor.close()
            except Exception as e:
                logging.error(f'Insert operation failed: {e}')
                self.Insert_status_lable.configure(text='check the accuracy of the entered data', fg_color='red')
                print("Ошибка выполнения запроса:", e)
                conn.rollback()
                cursor.close()

    def delete_button_event(self):
        cursor = conn.cursor()
        selected_table = self.Tables_optionemenu.get()
        selected_column = self.delete_option_menu.get()
        value_to_delete = self.delete_entry.get()
        logging.info(f'Delete operation started')

        if selected_table and selected_column and value_to_delete:

            delete_query = f"DELETE FROM {selected_table} WHERE {selected_column} = %s;"  # Подстановка метки параметра
            try:
                cursor.execute(delete_query, (value_to_delete,))
                affected_rows = cursor.rowcount  # Получение количества затронутых строк
                conn.commit()
                if affected_rows == 0:
                    logging.warning(f'No rows deleted')
                    self.Delete_status_lable.configure(text='No rows were deleted, check the accuracy of the entered data', fg_color='red')
                else:
                    logging.info(f'Deletion successful')
                    self.Delete_status_lable.configure(text='Deletion successful', fg_color='green')
                    self.table_show_button_event()
            except Exception as e:
                logging.error(f'Delete operation failed: {e}')
                self.Delete_status_lable.configure(text='check the accuracy of the entered data', fg_color='red')
                print("Ошибка выполнения запроса:", e)
                conn.rollback()
        else:
            logging.warning('Delete operation failed: not all fields filled')
            self.Delete_status_lable.configure(text='Fill fields', fg_color='red')

    def update_button_event(self):
        cursor = conn.cursor()
        selected_table = self.Tables_optionemenu.get()
        selected_column = self.Update_column_optionmenu.get()
        new_value = self.Update_value_entry.get()
        selected_column_condition = self.Update_column_optionmenu_condition.get()
        condition = self.condition.get()
        logging.info(f'Update operation started')

        if selected_table and selected_column and new_value:
            update_query = f"UPDATE {selected_table} SET {selected_column} = %s WHERE {selected_column_condition} = %s;"
            try:
                cursor.execute(update_query, (new_value, condition))
                affected_rows = cursor.rowcount
                conn.commit()
                if affected_rows == 0:
                    logging.warning(f'No rows updated')
                    self.Update_status_lable.configure(text='No rows were updated, check the accuracy of the entered data', fg_color='red')
                else:
                    logging.info(f'Update successful')
                    self.Update_status_lable.configure(text='Update successful', fg_color='green')
                    self.table_show_button_event()
            except Exception as e:
                logging.error(f'Update operation failed: {e}')
                self.Update_status_lable.configure(text='check the accuracy of the entered data', fg_color='red')
                print("Ошибка выполнения запроса:", e)
                conn.rollback()
        else:
            logging.warning('Update operation failed: not all fields filled')
            self.Update_status_lable.configure(text='Fill fields', fg_color='red')

    def column_has_constraints(self, table_name, column_name, constraints): ###
        global conn
        cursor = conn.cursor()
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' AND COLUMN_NAME = '{column_name}' AND COLUMNPROPERTY(OBJECT_ID(TABLE_NAME), COLUMN_NAME, 'IsIdentity') = 1;")
        result = cursor.fetchall()

        return bool(result)
    
    def get_columns_for_table(self, table_name):
        global conn
        cursor = conn.cursor()
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}';")
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        return columns
    
    def query(self):
        logging.info("Starting query execution")
        global conn
        cursor = conn.cursor()
        if not conn:
            logging.error("Connection error.")
            self.query_status_label.configure(text='CONNECTION ERROR. TRY RECONNECT', fg_color='red')
        else:
            selected_option = self.Query_optionemenu.get()
            if selected_option == "SelectOrdersByDateCondition":
                parameter_label_date = self.parameter_label_date.get() if self.parameter_label_date else ""
                query_text = f"EXEC SelectOrdersByDateCondition '{parameter_label_date}'"
            else:
                Optionmenu_text = self.Query_optionemenu.get()
                parameter_label = self.parameter_label.get() if self.parameter_label else ""
                parameter_label_date = self.parameter_label_date.get() if self.parameter_label_date else ""
                if Optionmenu_text == "GetServicesForOrder":
                    query_text = f"SELECT * FROM GetServicesForOrder({parameter_label});"
                elif Optionmenu_text == "SelectOrdersByReceiverAndDate":
                    query_text = f"EXEC SelectOrdersByReceiverAndDate {parameter_label}, '{parameter_label_date}';"
                elif Optionmenu_text == "InsertReceivers":
                    query_text = f"EXEC InsertReceivers '{parameter_label}', {parameter_label}"
                elif Optionmenu_text == "GetTotalOrdersForEmployee":
                    query_text = f"SELECT dbo.GetTotalOrdersForEmployee({parameter_label}) AS TotalOrders;"
                elif Optionmenu_text == "CalculateLensCost":
                    query_text = f"EXEC CalculateLensCost {parameter_label}"
                elif Optionmenu_text == "GetFramesSoldOnDate":
                    query_text = f"SELECT * FROM GetFramesSoldOnDate('{parameter_label_date}')"
                elif Optionmenu_text == "GetOrdersByCustomerFullName":
                    query_text = f"SELECT * FROM GetOrdersByCustomerFullName('{parameter_label}%')"
                elif Optionmenu_text == "GetTotalIncomeByMonthDay":
                    query_text = f"SELECT * FROM GetTotalIncomeByMonthDay ({parameter_label})"
                elif Optionmenu_text == "GetTotalOrdersByEmployee":
                    query_text = "SELECT * FROM GetTotalOrdersByEmployee()"
                elif Optionmenu_text == "CalculatePlannedCompletionDate":
                    query_text = "SELECT * FROM CalculatePlannedCompletionDate()"

            if Optionmenu_text == "InsertReceivers":
                try:
                    cursor.execute(query_text)
                    self.query_status_label.configure(text='successful', fg_color='green')
                    conn.commit()
                except:
                    self.query_status_label.configure(text='check the accuracy of the entered data', fg_color='red')
                    conn.rollback()
                    cursor.close()
            else:
                try:
                    cursor.execute(query_text)
                    result = cursor.fetchall()

                    headers = [column[0] for column in cursor.description]

                    self.Selected_query = customtkinter.CTkScrollableFrame(master=self.Query_frame, width=1310, height=750)
                    self.Selected_query.grid(row=8, column=0, padx=10, pady=5, sticky="n")

                    for col, header in enumerate(headers):
                        header_label = customtkinter.CTkLabel(self.Selected_query, text=header, font=("Arial", 10, "bold"))
                        header_label.grid(row=0, column=col, padx=10, pady=5)

                    for row_idx, row in enumerate(result):
                        for col_idx, header in enumerate(headers):
                            cell_value = row[header]
                            cell_label = customtkinter.CTkLabel(self.Selected_query, text=str(cell_value))
                            cell_label.grid(row=row_idx + 1, column=col_idx, padx=10, pady=5)

                    conn.commit()

                    self.query_status_label.configure(text='successful', fg_color='green')

                except Exception as e:
                    logging.error(f"Query execution failed: {e}")
                    self.query_status_label.configure(text='check the accuracy of the entered data', fg_color='red')
                    conn.rollback()
                    cursor.close()

    def update_query_parameters(self, selected_option): ###
        parameter_label = None
        parameter_label_date = None

        for widget in self.Query_frame.winfo_children():
            if isinstance(widget, customtkinter.CTkEntry):
                widget.destroy()
            elif isinstance(widget, DateEntry):
                widget.destroy()
        
        if selected_option == "GetServicesForOrder":
            logging.info('Creating parameter input for order number')
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="order number")
            parameter_label.grid(row=2, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "SelectOrdersByReceiverAndDate":
            logging.info('Creating parameter input for receiver code and order date')
            inf_label_date = customtkinter.CTkLabel(self.Query_frame, text="Order date:")
            inf_label_date.grid(row=3, column=0 ,padx=20, pady=10, sticky="n")
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="Receiver code")
            parameter_label.grid(row=2, column=0, padx=20, pady=10, sticky="n")
            parameter_label_date = DateEntry(self.Query_frame, width=12, background='darkblue', date_pattern='yyyy-MM-dd',
                                foreground='white', borderwidth=2)
            parameter_label_date.grid(row=4, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "SelectOrdersByDateCondition":
            inf_label_date = customtkinter.CTkLabel(self.Query_frame, text="Order date:")
            inf_label_date.grid(row=2, column=0 ,padx=20, pady=10, sticky="n")
            parameter_label_date = DateEntry(self.Query_frame, width=12, background='darkblue', date_pattern='yyyy-MM-dd',
                                foreground='white', borderwidth=2)
            parameter_label_date.grid(row=3, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "InsertReceivers":
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="FullName")
            parameter_label.grid(row=2, column=0, padx=20, pady=10, sticky="n")
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="Iteration count")
            parameter_label.grid(row=3, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "GetTotalOrdersForEmployee":
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="Employee code")
            parameter_label.grid(row=2, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "CalculateLensCost":
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="Lens code")
            parameter_label.grid(row=2, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "GetFramesSoldOnDate":
            inf_label_date = customtkinter.CTkLabel(self.Query_frame, text="Order date:")
            inf_label_date.grid(row=2, column=0 ,padx=20, pady=10, sticky="n")
            parameter_label_date = DateEntry(self.Query_frame, width=12, background='darkblue', date_pattern='yyyy-MM-dd',
                                foreground='white', borderwidth=2)
            parameter_label_date.grid(row=3, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "GetOrdersByCustomerFullName":
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="Customer full name")
            parameter_label.grid(row=2, column=0, padx=20, pady=10, sticky="n")
        elif selected_option == "GetTotalIncomeByMonthDay":
            parameter_label = customtkinter.CTkEntry(self.Query_frame, placeholder_text="Number of month")
            parameter_label.grid(row=2, column=0, padx=20, pady=10, sticky="n")

        self.parameter_label = parameter_label
        self.parameter_label_date = parameter_label_date


    def select_frame_by_name(self, name):
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.frame_2_button.configure(fg_color=("gray75", "gray25") if name == "frame_2" else "transparent")
        self.frame_3_button.configure(fg_color=("gray75", "gray25") if name == "frame_3" else "transparent")
        self.admin_panel_button.configure(fg_color=("gray75", "gray25") if name == "admin_panel" else "transparent")

        if name == "home":
            self.Query_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.Query_frame.grid_forget()
        if name == "frame_2":
            self.Table_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.Table_frame.grid_forget()
        if name == "frame_3":
            self.View_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.View_frame.grid_forget()
        if name == "admin_panel":
            self.Admin_panel_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.Admin_panel_frame.grid_forget()

    def home_button_event(self):
        self.select_frame_by_name("home")

    def frame_2_button_event(self):
        new_table_names = get_table_names_from_db()
        self.Tables_optionemenu["values"] = new_table_names
        self.Tables_optionemenu.set(new_table_names[0])
        self.select_frame_by_name("frame_2")

    def frame_3_button_event(self):
        new_view_names = get_view_names_from_db()
        self.Views_optionemenu["values"] = new_view_names
        self.Views_optionemenu.set(new_view_names[0])
        self.select_frame_by_name("frame_3")

    def admin_panel_button_event(self):
        self.select_frame_by_name("admin_panel")

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def table_show_button_event(self):
        selected_table = self.Tables_optionemenu.get()
        if selected_table:
            self.show_selected_table(selected_table)

    def view_show_button_event(self):
        selected_view = self.Views_optionemenu.get()
        if selected_view:
            self.show_selected_view(selected_view)

    def get_table_data(self, table_name):
        global conn
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name};")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        data = {'headers': columns, 'rows': rows}
        print("Data retrieved from database:", data)
        return data
    
    
    def show_selected_table(self, name):
        global conn
        if not conn:
            self.info_label.configure(text='CONNECTION ERROR. TRY RECONNECT', fg_color='red')
            logging.error(f"Connection error when trying to access table: {name}")
        else:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {name}")
                result = cursor.fetchall()

                if not result:
                    self.info_label.configure(text=f"No data found in view {name}")
                    logging.info(f"No data found in table")
                else:
                    headers = [column[0] for column in cursor.description]

                    self.table_frame = customtkinter.CTkScrollableFrame(master=self.Table_frame, width=1630, height=920)
                    self.table_frame.grid(row=2, column=0, padx=10, pady=5, sticky="n")
                    
                    for col, header in enumerate(headers):
                        header_label = customtkinter.CTkLabel(self.table_frame, text=header, font=("Arial", 10, "bold"))
                        header_label.grid(row=0, column=col, padx=10, pady=5)

                    for row_idx, row in enumerate(result):
                        for col_idx, header in enumerate(headers):
                            cell_value = row[header]
                            cell_label = customtkinter.CTkLabel(self.table_frame, text=str(cell_value))
                            cell_label.grid(row=row_idx + 1, column=col_idx, padx=10, pady=5)
                    
                    logging.info(f"Successfully displayed table {name}")

            except Exception as e:
                logging.error(f"Error while displaying table {name}: {str(e)}")

    def show_selected_view(self, name):
        global conn
        if not conn:
            self.info_label.configure(text='CONNECTION ERROR. TRY RECONNECT', fg_color='red')
            logging.error(f"Connection error when trying to access view")
        else:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {name}")
                result = cursor.fetchall()

                if not result:
                    self.info_label.configure(text=f"No data found in view {name}")
                    logging.info(f"No data found in view")
                else:
                
                    headers = [desc[0] for desc in cursor.description]

                    self.view_frame = customtkinter.CTkScrollableFrame(master = self.View_frame, width=1730, height=920)
                    self.view_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

                    for col, header in enumerate(headers):
                        header_label = customtkinter.CTkLabel(self.view_frame, text=header, font=("Arial", 10, "bold"))
                        header_label.grid(row=2, column=col, padx=10, pady=5)

                    for row_idx, row in enumerate(result):
                        for col_idx, header in enumerate(headers):
                            cell_value = row[header]
                            cell_label = customtkinter.CTkLabel(self.view_frame, text=str(cell_value))
                            cell_label.grid(row=row_idx + 3, column=col_idx, padx=10, pady=5)

                    self.scrollbar = customtkinter.CTkScrollbar(self.View_frame, orientation='horizontal')
                    self.scrollbar.grid(side = 'botom')
                    self.view_frame.config(self.scrollbar.set)
                    logging.info(f"Successfully displayed view {name}")

            except Exception as e:
                logging.error(f"Error while displaying view {name}: {str(e)}")

                
    def export_view(self):
        selected_view = self.Export_view_optionemenu.get()
        selected_format = self.export_format_optionmenu2.get()

        if selected_view:
            table_data = self.get_table_data(selected_view)
            export_time = datetime.now().strftime("%Y-%m-%d")
            table_name = f"{selected_view}_{export_time}"

            filetypes = []

            if selected_format == "PDF":
                filetypes = [("PDF files", "*.pdf")]
            elif selected_format == "Excel":
                filetypes = [("Excel files", "*.xlsx")]

            file_path = filedialog.asksaveasfilename(defaultextension=filetypes[0][1], filetypes=filetypes)

            if file_path:
                if selected_format == "PDF":
                    self.export_to_pdf(table_data, file_path, table_name)
                elif selected_format == "Excel":
                    self.export_to_excel(table_data, file_path, table_name)
                else:
                    print("No export format selected.")

    def export_table(self):
        selected_table = self.Export_table_optionemenu.get()
        selected_format = self.export_format_optionmenu.get()

        if selected_table:
            table_data = self.get_table_data(selected_table)
            export_time = datetime.now().strftime("%Y-%m-%d")
            table_name = f"{selected_table}_{export_time}"

            filetypes = []

            if selected_format == "PDF":
                filetypes = [("PDF files", "*.pdf")]
            elif selected_format == "Excel":
                filetypes = [("Excel files", "*.xlsx")]

            file_path = filedialog.asksaveasfilename(defaultextension=filetypes[0][1], filetypes=filetypes)

            if file_path:
                if selected_format == "PDF":
                    self.export_to_pdf(table_data, file_path, table_name)
                elif selected_format == "Excel":
                    self.export_to_excel(table_data, file_path, table_name)
                else:
                    print("No export format selected.")

    def export_to_pdf(self, data, file_path, table_name):
        try:
            df = pd.DataFrame(data['rows'], columns=data['headers'])
            html = f"<h2>{table_name}</h2>" + df.to_html()

            config = pdfkit.configuration(wkhtmltopdf=r'\wkhtmltopdf\bin\wkhtmltopdf.exe')

            pdfkit.from_string(html, file_path, configuration=config, options={'encoding': 'utf-8'})

            logging.info(f"PDF file {file_path} successfully created.")
        except Exception as e:
            logging.error(f"Error while exporting to PDF: {str(e)}")

    def export_to_excel(self, data, file_path, table_name):
        try:
            df = pd.DataFrame(data['rows'], columns=data['headers'])
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name=table_name)
            writer.close()

            logging.info(f"Excel file {file_path} successfully created.")
        except Exception as e:
            logging.error(f"Error while exporting to Excel: {str(e)}")

    

if __name__ == "__main__":
    combined_app = CombinedApp()
    combined_app.mainloop()