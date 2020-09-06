import os
import docker


def start_firefox():

    container_time_zone = os.getenv('CONTAINERTZ', "TZ=US/Mountain")

    client = docker.from_env()
    client.containers.run(
        "selenium/standalone-firefox:4.0.0-alpha-7-prerelease-20200826",
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
