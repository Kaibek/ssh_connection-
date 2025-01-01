import paramiko
import os
import logging
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

# Этот скрипт предназначен для автоматизации процесса, для получения метрики,
# создания бэкапа Zabbix на сервере и скачивания бэкапа на локальную машину или ПК.

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)



def check_system_metrics(ssh, local_metric_path):

    try:
        commands = [
            f"top -bn1 | grep 'Cpu(s)'",
            f"free -m",
            f"vnstat -i any",
            f"netstat -s",
            f"df -h"
        ]

        all_metrics = ""

        for command in commands:
            stdin, stdout, stderr = ssh.exec_command(command)
            all_metrics += f"Результат выполнения команды '{command}':\n{stdout.read().decode()}\n"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metric_filename = f"server_metrics_{timestamp}.txt"
        local_metric_full_path = os.path.join(local_metric_path, metric_filename)

        with open(local_metric_full_path, "w") as file:
            file.write(all_metrics)

        logger.info(f"Метрики собраны и сохранены в файл: {local_metric_full_path}")

    except Exception as e:
        logger.error(f"Не удалось собрать метрики: {e}")



def create_zabbix_backup(ssh, backup_folder, zabbix_data_path, password):

    # Путь и имя для резервной копии
    backup_file = f"zabbix_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.tgz"
    backup_path = f"{backup_folder}/{backup_file}"

    # Команда для создания бэкапа
    command = f"echo {password} | sudo -S tar -C {zabbix_data_path} -czf {backup_path} ."

    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        stderr_output = stderr.read().decode()

        if stderr_output:
            logger.warning(f"Ошибка при выполнении команды: {stderr_output}")

        logger.info(f"Резервная копия создана: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Ошибка при создании резервной копии: {e}")
        return None



def download_backup_from_server(ssh, remote_path, local_path):

    try:
        with ssh.open_sftp() as sftp:
            sftp.get(remote_path, local_path)

        logger.info(f"Резервная копия скачана: {local_path}")

    except FileNotFoundError:
        logger.error(f"Файл не найден на сервере: {remote_path}")

    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {e}")



def ssh_connection(ip_address, username, password, local_backup_path, local_metric_path, zabbix_data_path):

    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(ip_address, username=username, password=password)
            logger.info(f"Successfully connected to {ip_address}")

            check_system_metrics(ssh, local_metric_path)

            backup_folder = "/tmp/zabbix_backup"
            remote_backup_path = create_zabbix_backup(ssh, backup_folder, zabbix_data_path, password)

            if remote_backup_path:
                download_backup_from_server(ssh, remote_backup_path, local_backup_path)

        except paramiko.AuthenticationException as error:
            logger.error(f"Incorrect data {error} to {ip_address}")

        except paramiko.SSHException as error:
            logger.error(f"Failed {error} to connect to {ip_address}")

        except Exception as error:
            logger.error(f"{error}")



class SSHApp:
    def __init__(self, root):

        self.root = root
        self.root.title("SSH Connection App")
        self.root.geometry("500x350")


        self.label_ip = tk.Label(self.root, text="IP адрес")
        self.label_ip.grid(row=0, column=0, padx=10, pady=10)
        self.entry_ip = tk.Entry(self.root)
        self.entry_ip.grid(row=0, column=1, padx=10, pady=10)


        self.label_username = tk.Label(self.root, text="Логин")
        self.label_username.grid(row=1, column=0, padx=10, pady=10)
        self.entry_username = tk.Entry(self.root)
        self.entry_username.grid(row=1, column=1, padx=10, pady=10)


        self.label_password = tk.Label(self.root, text="Пароль")
        self.label_password.grid(row=2, column=0, padx=10, pady=10)
        self.entry_password = tk.Entry(self.root, show="*")
        self.entry_password.grid(row=2, column=1, padx=10, pady=10)


        self.label_backup_path = tk.Label(self.root, text="Путь для бэкапов")
        self.label_backup_path.grid(row=3, column=0, padx=10, pady=10)
        self.entry_backup_path = tk.Entry(self.root)
        self.entry_backup_path.grid(row=3, column=1, padx=10, pady=10)
        self.button_browse_backup = tk.Button(self.root, text="Обзор", command=self.browse_backup)
        self.button_browse_backup.grid(row=3, column=2, padx=10, pady=10)


        self.label_metric_path = tk.Label(self.root, text="Путь для метрик")
        self.label_metric_path.grid(row=4, column=0, padx=10, pady=10)
        self.entry_metric_path = tk.Entry(self.root)
        self.entry_metric_path.grid(row=4, column=1, padx=10, pady=10)
        self.button_browse_metric = tk.Button(self.root, text="Обзор", command=self.browse_metric)
        self.button_browse_metric.grid(row=4, column=2, padx=10, pady=10)


        self.label_zabbix_data_path = tk.Label(self.root, text="Путь к данным Zabbix")
        self.label_zabbix_data_path.grid(row=5, column=0, padx=10, pady=10)
        self.entry_zabbix_data_path = tk.Entry(self.root)
        self.entry_zabbix_data_path.grid(row=5, column=1, padx=10, pady=10)
        self.button_browse_zabbix_data = tk.Button(self.root, text="Обзор", command=self.browse_zabbix_data)
        self.button_browse_zabbix_data.grid(row=5, column=2, padx=10, pady=10)


        self.button_connect = tk.Button(self.root, text="Подключиться", command=self.connect_ssh)
        self.button_connect.grid(row=6, column=0, columnspan=3, pady=20)



    def browse_backup(self):

        backup_path = filedialog.askdirectory(title="Выберите папку для бэкапов")


        if backup_path:
            self.entry_backup_path.delete(0, tk.END)
            self.entry_backup_path.insert(0, backup_path)



    def browse_metric(self):

        metric_path = filedialog.askdirectory(title="Выберите папку для метрик")

        if metric_path:
            self.entry_metric_path.delete(0, tk.END)
            self.entry_metric_path.insert(0, metric_path)

    def browse_zabbix_data(self):

        zabbix_data_path = filedialog.askdirectory(title="Выберите папку с данными Zabbix")


        if zabbix_data_path:
            if not os.path.exists(zabbix_data_path):
                messagebox.showerror("Ошибка", "Выбранный путь недействителен!")
                return

            if not os.listdir(zabbix_data_path):
                messagebox.showerror("Ошибка", "Выбранная директория пуста. Укажите правильный путь к данным Zabbix!")
                return


            self.entry_zabbix_data_path.delete(0, tk.END)
            self.entry_zabbix_data_path.insert(0, zabbix_data_path)



    def connect_ssh(self):

        ip = self.entry_ip.get()
        username = self.entry_username.get()
        password = self.entry_password.get()
        backup_path = self.entry_backup_path.get()
        metric_path = self.entry_metric_path.get()
        zabbix_data_path = self.entry_zabbix_data_path.get()


        if "/var/lib/docker/volumes" in zabbix_data_path:
            zabbix_volume_name = os.path.basename(zabbix_data_path)
            use_volume = True

        else:
            zabbix_volume_name = zabbix_data_path  # Если не volume, то это обычный путь
            use_volume = False

        if not ip or not username or not password or not zabbix_data_path:
            messagebox.showerror("Ошибка",
                                 "Пожалуйста, заполните все обязательные поля!")
            return


        local_backup_path = os.path.join(backup_path, "backup.tgz")
        local_metric_path = os.path.join(metric_path)


        if not os.path.exists(local_metric_path):
            os.makedirs(local_metric_path)

        try:
            ssh_connection(ip, username, password, local_backup_path, local_metric_path, zabbix_data_path)
            messagebox.showinfo("Успех", "Подключение и выполнение задач завершены успешно!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")




if __name__ == "__main__":

    root = tk.Tk()
    app = SSHApp(root)
    root.mainloop()



