import os
import docker

container_time_zone = os.getenv('CONTAINERTZ', 'TZ=US/Mountain')

opera_docker_version = os.getenv(
    'OPERADOCKERVERSION', 'selenium/standalone-opera:latest')
chrome_docker_version = os.getenv(
    'CHROMEDOCKERVERSION', 'selenium/standalone-chrome:latest')
firefox_docker_version = os.getenv(
    'FIREFOXDOCKERVERSION', 'selenium/standalone-firefox:latest')


def start_firefox():

    client = docker.from_env()
    client.containers.run(
        firefox_docker_version,
        ports={'4444/tcp': 4444, '5900/tcp': 5900},
        volumes={'/dev/shm': {'bind': '/dev/shm', 'mode': 'rw'}, },
        detach=True,
        remove=True,
        auto_remove=True,
        environment=[container_time_zone])


def start_chrome():

    client = docker.from_env()
    client.containers.run(
        chrome_docker_version,
        ports={'4444/tcp': 4444, '5900/tcp': 5900},
        volumes={'/dev/shm': {'bind': '/dev/shm', 'mode': 'rw'}, },
        detach=True,
        remove=True,
        auto_remove=True,
        environment=[container_time_zone])


def start_opera():

    client = docker.from_env()
    client.containers.run(
        opera_docker_version,
        ports={'4444/tcp': 4444, '5900/tcp': 5900},
        volumes={'/dev/shm': {'bind': '/dev/shm', 'mode': 'rw'}, },
        detach=True,
        remove=True,
        auto_remove=True,
        environment=[container_time_zone])


def stop_selenium_containers():
    client = docker.from_env()
    image_name = "selenium/standalone"

    for container in client.containers.list():
        if image_name in str(container.image.tags):
            container.stop()
