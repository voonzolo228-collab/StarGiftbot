from setuptools import setup, find_packages

setup(
    name='gift-bot',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'Flask',
        'PyTelegramBotAPI',
        'Telethon',
        'aiohttp',
        'pydantic==2.5.0',
        'pydantic-core==2.14.5'
    ]
)
