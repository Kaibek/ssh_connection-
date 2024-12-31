import paramiko
import os
import logging
from datetime import datetime

#Этот скрипт предназначен для автоматизации процесса, для получения метрики, создание бэкапа Zabbix на сервере
#и cкачивание бэкапа на локальную машину или ПК.


# Настройка логгера 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)



def check_system_metrics(ssh, local_metric_path):
# Проверка использование CPU и RAM на сервере через SSH
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



def create_zabbix_backup(ssh, backup_folder):
    # Создает резервную копию Zabbix на сервере и возвращает путь к архиву (.tgz).
    backup_file = f"zabbix_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.tgz"
    backup_path = f"{backup_folder}/{backup_file}"

    # Команды для создания резервной копии с использованием tar
    commands = [
        f"mkdir -p {backup_folder}",
        f"echo {password} | sudo -S tar -C /var/lib/docker/volumes/zabbix-docker_zabbix_postgresql_data -czf {backup_path} ."
    ]

    try:
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stderr_output = stderr.read().decode()

            if stderr_output:

                logger.warning(f"Ошибка при выполнении команды: {stderr_output}")

        logger.info(f"Резервная копия создана: {backup_path}")

        return backup_path

    except Exception as e:
        logger.error(f"Ошибка при создании резервной копии: {e}")
        return None



def download_backup_from_server(ssh, remote_path, local_path):
# Скачивает резервную копию с сервера на локальный ПК.

    try:
        with ssh.open_sftp() as sftp:
            sftp.get(remote_path, local_path, )

        logger.info(f"Резервная копия скачана: {local_path}")

    except FileNotFoundError:
        logger.error(f"Файл не найден на сервере: {remote_path}")

    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {e}")



def ssh_connection(ip_address, username, password, local_backup_path, local_metric_path):

    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(ip_address, username=username, password=password)
            logger.info(f"Successfully connected to {ip_address}")

            check_system_metrics(ssh, local_metric_path)

            backup_folder = "/tmp/zabbix_backup"
            remote_backup_path = create_zabbix_backup(ssh, backup_folder)

            if remote_backup_path:
                download_backup_from_server(ssh, remote_backup_path, local_backup_path)

        except paramiko.AuthenticationException as error:
            logger.error(f" Incorrect data {error} to {ip_address}")

        except paramiko.SSHException as error:
            logger.error(f"Failed {error} to connect to {ip_address}")

        except Exception as error:
            logger.error(f" {error}")


# Основная логика
if __name__ == "__main__":
    # Данные для подключения
    server_ip = "192.168.1.1"
    username = "admin"
    password = "12345"

    # Локальный путь для сохранения резервной копии
    desktop_path = r"C:\Users\User\Desktop"
    local_backup_path = os.path.join(desktop_path, "backup.tgz")
    local_metric_path = os.path.join(desktop_path)

    if not os.path.exists(local_metric_path):
        os.makedirs(local_metric_path)

    ssh_connection(server_ip, username, password, local_backup_path, local_metric_path)


