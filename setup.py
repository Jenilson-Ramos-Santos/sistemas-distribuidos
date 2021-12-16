from setuptools import setup

setup(
    name='projeto-sd',
    description='Projeto desenvolvido na disciplina de Sistemas Distribuídos',
    author='Jenilson Ramos',
    install_requires=['fastapi', 'uvicorn', 'pydantic', 'requests'],
    packages=['app'],
    entry_points={
        'console_scripts': [
            'acervo-sd=app.app:main',
        ]
    }
)
