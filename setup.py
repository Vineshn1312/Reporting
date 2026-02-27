from setuptools import setup, find_packages

setup(
    name="reportly",
    version="1.0.0",
    description="Modern multi-platform test reporting tool for Selenium & Appium with AI-powered failure analysis",
    author="Reportly",
    packages=find_packages(),
    include_package_data=True,
    package_data={"reportly": ["templates/*.html"]},
    python_requires=">=3.8",
    install_requires=[
        "Jinja2>=3.1.2",
        "openai>=1.0.0",
        "Pillow>=10.0.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "selenium": ["selenium>=4.15.0"],
        "appium": ["Appium-Python-Client>=3.0.0"],
        "all": ["selenium>=4.15.0", "Appium-Python-Client>=3.0.0"],
    },
)
