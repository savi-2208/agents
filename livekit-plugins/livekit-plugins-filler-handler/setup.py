from setuptools import setup, find_namespace_packages

setup(
    name="livekit-plugins-filler-handler",
    version="0.1.0",
    description="Filler word interruption handler for LiveKit Agents",
    packages=find_namespace_packages(include=["livekit.*"]),
    install_requires=[
        "livekit>=0.10.0",
        "livekit-agents>=1.0.0",
    ],
    python_requires=">=3.9",
    # Important: This tells setuptools to use namespace packages
    zip_safe=False,
)