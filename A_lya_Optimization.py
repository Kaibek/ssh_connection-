import paramiko
import logging

logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

def check_system(ssh):
    try:
        stdin, stdout, stderr = ssh.exec_command('top -bn1 | grep "Cpu(s)" && free -m')
        output = stdout.read().decode("utf-8")
        logger.info(f"System metric: \n{output}")
    except Exception as e:
        logger.error(f"Произошла ошибок метрик! \n{e}")


def ssh_connection(ip_addres, username, password):
    with paramiko.SSHClient() as ssh:

        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(ip_addres, username=username, password=password)

            check_system(ssh)

        except paramiko.AuthenticationException:
            print("Authentication Failed")
        except paramiko.SSHException as e:
            print(f"failed: {e}")
        except Exception as e:
            print(f"failed: {e}")


if __name__ == '__main__':
    ip_address = "192.168.1.111"
    username = "zabbix"
    password = "12345"

    ssh_connection(ip_address, username, password)



