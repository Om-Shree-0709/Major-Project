import os
import psutil
import platform


class SystemDiagnostics:

    def check_cpu(self):
        return psutil.cpu_percent(interval=1)

    def check_memory(self):
        memory = psutil.virtual_memory()
        return memory.percent

    def check_disk(self):
        disk = psutil.disk_usage("/")
        return disk.percent

    def system_info(self):

        return {
            "platform": platform.system(),
            "python_version": platform.python_version()
        }


if __name__ == "__main__":

    diag = SystemDiagnostics()

    print("CPU:", diag.check_cpu())
    print("Memory:", diag.check_memory())
    print("Disk:", diag.check_disk())