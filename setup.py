from setuptools import setup, find_packages

setup(
    name="egucalendarextractor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyMuPDF>=1.22.0",
        "matplotlib",
        "numpy",
        "streamlit"
    ],
    entry_points={
        "console_scripts": [
            "egucalendar=egucalendarextractor.core:main",
        ],
    },
    author="Your Name",
    description="EGU PDF calendar to .ics converter",
    url="https://github.com/yourusername/egucalendarextractor",
    license="CC-BY-NC-4.0",
    python_requires=">=3.7",
)
