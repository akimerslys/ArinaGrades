call:
	docker stop $$(docker ps -qf "ancestor=arinagrades")
	docker rm $$(docker ps -aqf "ancestor=arinagrades")
	docker rmi arinagrades
	docker build -t arinagrades .
	docker run arinagrades

.PHONY:
build:
	docker build -t arinagrades .
	docker run arinagrades

.PHONY:
clear:
	docker system prune -a
