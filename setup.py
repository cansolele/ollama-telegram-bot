from setuptools import setup, find_packages
import os


def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [
            line.strip() for line in file if line.strip() and not line.startswith("#")
        ]


def create_systemd_service():
    service_content = """[Unit]
Description=Ollama Telegram Bot
After=network.target ollama.service

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={work_dir}
Environment=PYTHONUNBUFFERED=1
ExecStart={python_path} {main_script}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    try:
        # Get current user and group
        user = os.getenv("SUDO_USER", os.getenv("USER", "root"))
        group = user

        # Get Python path
        python_path = os.path.join("/usr/bin/python3")

        # Get working directory and main script path
        work_dir = os.path.abspath(os.path.dirname(__file__))
        main_script = os.path.join(work_dir, "main.py")

        # Format service content
        service_content = service_content.format(
            user=user,
            group=group,
            work_dir=work_dir,
            python_path=python_path,
            main_script=main_script,
        )

        # Write service file
        service_path = "/etc/systemd/system/ollama-bot.service"
        if os.path.exists("/etc/systemd/system"):
            with open(service_path, "w") as f:
                f.write(service_content)
            os.chmod(service_path, 0o644)
            os.system("systemctl daemon-reload")
            print(f"\nSystemd service created at {service_path}")
            print("To start the bot, run:")
            print("sudo systemctl enable ollama-bot")
            print("sudo systemctl start ollama-bot")
            print("\nTo check status:")
            print("sudo systemctl status ollama-bot")
    except Exception as e:
        print(f"\nError creating systemd service: {e}")
        print("Please run: sudo pip install -e .")


setup(
    name="ollama-telegram-bot",
    version="2.0.0",
    packages=find_packages(),
    install_requires=read_requirements("requirements.txt"),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "ollama-bot=main:main",
        ],
    },
)
