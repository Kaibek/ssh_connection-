import paramiko
import datetime
import os
import logging
#Этот скрипт предназначен для автоматизации процесса, для получения метрики, создание бэкапа Zabbix на сервере# и cкачивание бэкапа на локальную машину или ПК.


# Настройка логгера 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_system_metrics(ssh):
# Проверка использование CPU и RAM на сервере через SSH


    try:
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' && free -m")
        output = stdout.read().decode()
        logger.info(f"Системные метрики:\n{output}")

    except Exception as e:
        logger.error(f"Ошибка при получении метрик: {e}")



def create_zabbix_backup(ssh, backup_folder):
    # Создает резервную копию Zabbix на сервере и возвращает путь к архиву (.tgz).
    backup_file = f"zabbix_backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.tgz"
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
            sftp.get(remote_path, local_path)

        logger.info(f"Резервная копия скачана: {local_path}")

    except FileNotFoundError:
        logger.error(f"Файл не найден на сервере: {remote_path}")

    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {e}")


# Основная логика
if __name__ == "__main__":
    # Данные для подключения
    server_ip = "10.7.5.2"
    username = "Docker"
    password = "password"

    # Локальный путь для сохранения резервной копии
    desktop_path = r"C:\Users\User\Desktop"
    local_backup_path = os.path.join(desktop_path, "backup.tgz")


    # Подключение к серверу
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


        try:
            ssh.connect(server_ip, username=username, password=password)

            # 1. Проверка системных метрик
            check_system_metrics(ssh)

            # 2. Создание резервной копии
            backup_folder = "/tmp/zabbix_backup"
            remote_backup_path = create_zabbix_backup(ssh, backup_folder)

            # 3. Скачивание резервной копии на локальный ПК
            if remote_backup_path:
                download_backup_from_server(ssh, remote_backup_path, local_backup_path)

        except paramiko.AuthenticationException:
            logger.error("Ошибка: Неверные учетные данные для SSH-подключения.")

        except paramiko.SSHException as e:
            logger.error(f"Ошибка SSH: {e}")

        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
