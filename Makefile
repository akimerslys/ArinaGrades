call:
	docker stop $$(docker ps -qf "ancestor=arinagrades")
	docker rm $$(docker ps -aqf "ancestor=arinagrades")
	docker rmi arinagrades
	docker build -t arinagrades .
	docker run aringrades
